"""Explicitly synthetic fixture for local backup/antivirus verification."""
import io
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from pypdf import PdfWriter
from Pacientes.models import Paciente, PrivacyNotice, ConsentTemplate, ConsentEvidence
from Usuarios.models import Clinic, ClinicMembership, AuditEvent
from api.privacy import NOTICE_FIELDS
from api.services.document_integrity import seal, file_digest
from api.services.document_payloads import notice_payload, template_payload, evidence_payload
from api.services.file_inspection import queue
import uuid


class Command(BaseCommand):
    help = 'Create synthetic development-only documents for the stage 3 restore drill.'

    @transaction.atomic
    def handle(self, *args, **options):
        if settings.SETTINGS_MODULE != 'SmileManager.settings_local':
            raise CommandError('This fixture is restricted to local development.')
        clinic, _ = Clinic.objects.get_or_create(slug='stage3-synthetic-drill', defaults={'name': 'Clínica sintética etapa 3', 'status': 'ACTIVE'})
        user, created = User.objects.get_or_create(username='stage3_synthetic_operator', defaults={'first_name': 'Operador', 'last_name': 'Sintético', 'is_active': False})
        if created:
            user.set_unusable_password()
            user.save(update_fields=['password'])
        ClinicMembership.objects.get_or_create(user=user, clinic=clinic, defaults={'role': 'DOCTOR', 'status': 'ACTIVE'})
        patient, _ = Paciente.objects.get_or_create(clinic=clinic, medico=user, email='stage3-synthetic@example.test', defaults={
            'nombre': 'Paciente', 'appat': 'Sintético', 'apmat': 'Prueba', 'fecha_nacimiento': '2000-01-01', 'genero': 'F', 'telefono': '0000000000'})
        if ConsentEvidence.objects.filter(clinic=clinic).exists():
            self.stdout.write('Synthetic fixture already exists.')
            return
        notice = PrivacyNotice(clinic=clinic, version=1, body={key: ('synthetic@example.test' if key == 'privacy_email' else 'Dato sintético para simulacro; sin validez clínica.') for key in NOTICE_FIELDS}, approved_by=user, approved_name=user.get_full_name())
        notice.content_sha256, notice.integrity_seal = seal(notice_payload(notice))
        notice.save()
        template = ConsentTemplate(clinic=clinic, version=1, kind='CLINICAL', title='Documento sintético para restauración', text='Exclusivamente para pruebas técnicas; sin validez clínica.', approved_by=user, approved_name=user.get_full_name())
        template.content_sha256, template.integrity_seal = seal(template_payload(template))
        template.save()
        writer, output = PdfWriter(), io.BytesIO()
        writer.add_blank_page(width=100, height=100)
        writer.write(output)
        upload = ContentFile(output.getvalue(), name='synthetic.pdf')
        row = ConsentEvidence(clinic=clinic, patient=patient, template=template, template_sha256=template.content_sha256,
                              recorded_by=user, recorded_name=user.get_full_name(), recorded_at=timezone.now(), signer_name='Firmante Sintético',
                              signer_role='PATIENT', signed_on=timezone.localdate(), signed_document=upload, file_sha256=file_digest(upload))
        row.content_sha256, row.integrity_seal = seal(evidence_payload(row))
        row.save()
        queue(row.signed_document.name, row.file_sha256)
        AuditEvent.objects.create(clinic=clinic, actor=user, action='SYNTHETIC_RESTORE_FIXTURE', request_id=uuid.uuid4())
        self.stdout.write('Synthetic PDF queued for real antivirus inspection.')
