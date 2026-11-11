"""Explicitly synthetic legal/document configuration for isolated tests only."""
from django.utils import timezone
from Pacientes.models import PrivacyNotice, ConsentTemplate
from api.privacy import NOTICE_FIELDS
from api.services.document_integrity import seal
from api.services.document_payloads import notice_payload, template_payload


def publish_documents(clinic, user):
    if not user.get_full_name().strip():
        user.first_name, user.last_name = 'Persona', 'Sintética'
        user.save(update_fields=['first_name', 'last_name'])
    notice = PrivacyNotice(clinic=clinic, version=1, body={key: ('privacy@example.test' if key == 'privacy_email' else f'Dato sintético para {key}; no utilizar en producción.') for key in NOTICE_FIELDS}, approved_by=user, approved_name=user.get_full_name())
    notice.content_sha256, notice.integrity_seal = seal(notice_payload(notice))
    notice.save()
    template = ConsentTemplate(clinic=clinic, kind='CLINICAL', version=1, title='Consentimiento sintético de prueba',
                               text='Documento sintético para comprobar evidencia. No utilizar en atención real.',
                               approved_by=user, approved_name=user.get_full_name())
    template.content_sha256, template.integrity_seal = seal(template_payload(template))
    template.save()
    return notice, template


def evidence_values(template, upload):
    return {'template_id': template.pk, 'signer_name': 'Paciente Sintético', 'signer_role': 'PATIENT',
            'signed_on': timezone.localdate().isoformat(), 'attested': True, 'signed_document': upload}


def signed_pdf_bytes():
    from io import BytesIO
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def scan_test_documents():
    # Mock only the antivirus transport; run the real bounded PDF parser.
    from unittest.mock import patch
    from api.services.file_inspection import process_one
    with patch('api.services.file_inspection.clamav', return_value=True):
        while process_one():
            pass
