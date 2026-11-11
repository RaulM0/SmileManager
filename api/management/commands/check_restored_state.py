import json
from django.apps import apps
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError
from api.management.commands.audit_storage_consistency import FIELDS
from Usuarios.audit_integrity import verify
from api.services.document_integrity import file_digest, verify as verify_document
from api.services import document_payloads
from DiagnosticosIA.models import AIAnalysisRun
from Pacientes.models import PrivacyNotice, ConsentTemplate, ConsentRevocation, ConsultationAddendum, ClinicalRevision, Consulta
from api.tenant_consent_evidence import revocation_payload
from Pacientes.models import ConsentEvidence
from Usuarios.models import AuditEvent, FileInspection
from api.services.file_inspection import signature
import hmac
from django.conf import settings


class Command(BaseCommand):
    help = 'Fail on missing referenced files or altered sealed audit/evidence; report only counts.'

    def handle(self, *args, **options):
        missing = invalid = 0
        for model, fields in FIELDS.items():
            for field in fields:
                for name in model.objects.exclude(**{field: ''}).exclude(**{field + '__isnull': True}).values_list(field, flat=True).iterator():
                    missing += int(not default_storage.exists(name))
        for name in AIAnalysisRun.objects.exclude(result_name='').values_list('result_name', flat=True).iterator():
            missing += int(not default_storage.exists(name))
        for model, payload in [(PrivacyNotice, document_payloads.notice_payload), (ConsentTemplate, document_payloads.template_payload),
                               (ConsentEvidence, document_payloads.evidence_payload), (ConsentRevocation, revocation_payload),
                               (ConsultationAddendum, document_payloads.addendum_payload), (ClinicalRevision, document_payloads.revision_payload),
                               (Consulta, document_payloads.consultation_payload)]:
            for row in model.objects.exclude(integrity_seal='').iterator():
                invalid += int(not verify_document(payload(row), row.content_sha256, row.integrity_seal))
        for event in AuditEvent.objects.exclude(integrity_seal='').iterator():
            invalid += int(not verify(event))
        for row in ConsentEvidence.objects.iterator():
            if default_storage.exists(row.signed_document.name):
                with default_storage.open(row.signed_document.name, 'rb') as file:
                    invalid += int(file_digest(file) != row.file_sha256)
        for row in FileInspection.objects.filter(status='CLEAN').iterator():
            valid_seal = row.checked_at and any(hmac.compare_digest(row.seal, signature(row, key)) for key in settings.FILE_SCAN_KEYS)
            invalid += int(not valid_seal)
            if default_storage.exists(row.storage_name):
                with default_storage.open(row.storage_name, 'rb') as file:
                    invalid += int(file_digest(file) != row.expected_sha256)
            else:
                missing += 1
        if missing or invalid:
            raise CommandError(f'Restore integrity failure: missing={missing} invalid={invalid}')
        counts = {model._meta.label: model.objects.count() for model in apps.get_models()}
        self.stdout.write(json.dumps({'counts': counts, 'missing': missing, 'invalid': invalid}, sort_keys=True))
