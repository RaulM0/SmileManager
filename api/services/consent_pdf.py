"""Generate consent documents without URLs, external assets or HTML input."""
from io import BytesIO
from xml.sax.saxutils import escape

from django.core.files.base import ContentFile
from django.utils import timezone
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def attach_consent_pdf(consent):
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    patient = consent.paciente
    paragraphs = [Paragraph('Consentimiento informado', styles['Title'])]
    for text in (
        patient.clinic.name,
        f'Paciente: {patient.nombre} {patient.appat} {patient.apmat}',
        f'Médico: {consent.medico.get_full_name() or consent.medico.username}',
        f'Aceptado: {timezone.localtime(consent.fecha_aceptacion).isoformat()}',
        consent.texto,
    ):
        paragraphs.extend((Spacer(1, 12), Paragraph(escape(text).replace('\n', '<br/>'), styles['BodyText'])))
    SimpleDocTemplate(buffer).build(paragraphs)
    consent.pdf_generado.save('consentimiento.pdf', ContentFile(buffer.getvalue()), save=False)
