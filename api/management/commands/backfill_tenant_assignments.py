"""Apply an explicitly reviewed migration manifest, in a maintenance window."""
import hashlib
import json
import tempfile
import uuid
from collections import Counter
from io import StringIO
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import OperationalError, connection, transaction

from Citas.models import Cita
from DiagnosticosIA.models import AIAnalysisRun
from Pacientes.models import (AntescedentesMedicos, ClinicalRevision, Consulta,
                              Consentimiento, EstudioComparativo, ImagenesClinicas,
                              Odontograma, Paciente)
from Usuarios.models import AuditEvent, Clinic, ClinicMembership, PlatformAdmin


class Command(BaseCommand):
    help = 'Validate or apply an explicitly reviewed patient assignment manifest.'

    def add_arguments(self, parser):
        parser.add_argument('--manifest', required=True)
        parser.add_argument('--apply', action='store_true')
        parser.add_argument('--expected-sha256')
        parser.add_argument('--actor-id', type=int)
        parser.add_argument('--maintenance-confirmed', action='store_true')
        parser.add_argument('--backup-confirmed', action='store_true')
        parser.add_argument('--lock-timeout-seconds', type=int, default=5)

    def handle(self, *args, **options):
        try:
            path = Path(options['manifest'])
            with path.open('rb') as source:
                contents = source.read(1_000_001)
            if len(contents) > 1_000_000:
                raise CommandError('Manifest exceeds the size limit.')
        except OSError as exc:
            raise CommandError('Cannot read manifest.') from exc
        digest = hashlib.sha256(contents).hexdigest()
        if options['apply']:
            if connection.vendor != 'postgresql':
                raise CommandError('Applying assignments requires PostgreSQL.')
            if not options['maintenance_confirmed'] or not options['backup_confirmed']:
                raise CommandError('Applying requires maintenance and verified backup confirmations.')
            if not options['expected_sha256'] or options['expected_sha256'].lower() != digest:
                raise CommandError('Manifest SHA-256 does not match the reviewed digest.')
            if not options['actor_id']:
                raise CommandError('Applying requires an explicit platform administrator actor.')
            if not 1 <= options['lock_timeout_seconds'] <= 60:
                raise CommandError('Lock timeout must be between 1 and 60 seconds.')

        # Validate a temporary snapshot, not the original path that an operator
        # might replace between review, validation, and the transaction.
        with tempfile.TemporaryDirectory(prefix='smile-tenant-manifest-') as directory:
            snapshot = Path(directory) / 'manifest.json'
            snapshot.write_bytes(contents)
            if not options['apply']:
                call_command('validate_tenant_assignments', manifest=str(snapshot), stdout=StringIO())
                self.stdout.write(f'dry_run=true manifest_sha256={digest} writes=0')
                return

            models = (get_user_model(), Clinic, ClinicMembership, PlatformAdmin, Paciente, Cita,
                      AntescedentesMedicos, Consulta, Consentimiento, EstudioComparativo,
                      ImagenesClinicas, Odontograma, ClinicalRevision, AIAnalysisRun, AuditEvent)
            tables = sorted({model._meta.db_table for model in models})
            with transaction.atomic():
                # Drains existing writers and prevents new ones while all relationships
                # are checked and updated. Readers can continue in PostgreSQL.
                quoted = ', '.join(connection.ops.quote_name(table) for table in tables)
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT set_config('lock_timeout', %s, true)", [f"{options['lock_timeout_seconds']}s"])
                        cursor.execute(f'LOCK TABLE {quoted} IN SHARE ROW EXCLUSIVE MODE')
                except OperationalError as exc:
                    raise CommandError('Could not acquire migration locks within the configured timeout; no data was changed.') from exc
                actor = get_user_model().objects.filter(pk=options['actor_id'], is_active=True,
                                                       platform_admin__is_active=True).first()
                if actor is None:
                    raise CommandError('Actor is not an active platform administrator.')
                call_command('validate_tenant_assignments', manifest=str(snapshot), stdout=StringIO())
                mappings = json.loads(contents.decode('utf-8-sig'))
                counts = Counter()
                request_id = uuid.uuid4()
                for row in mappings:
                    patient_id, clinic_id = row['patient_id'], uuid.UUID(str(row['clinic_id']))
                    counts['patients'] += Paciente.objects.filter(pk=patient_id, clinic__isnull=True).update(clinic_id=clinic_id)
                    counts['revisions'] += ClinicalRevision.objects.filter(patient_id=patient_id, clinic__isnull=True).update(clinic_id=clinic_id)
                    counts['ai_runs'] += AIAnalysisRun.objects.filter(image__paciente_id=patient_id, clinic__isnull=True).update(clinic_id=clinic_id)
                for clinic_id in sorted({uuid.UUID(str(row['clinic_id'])) for row in mappings}, key=str):
                    AuditEvent.objects.create(actor=actor, clinic_id=clinic_id, action='TENANT_BACKFILL_BATCH_APPLIED',
                                              resource_type='clinic', resource_id=str(clinic_id), request_id=request_id)
            self.stdout.write(f'dry_run=false manifest_sha256={digest} patients={counts["patients"]} '
                              f'revisions={counts["revisions"]} ai_runs={counts["ai_runs"]} request_id={request_id}')
