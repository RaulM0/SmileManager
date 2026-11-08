"""Eventos seleccionados, sin copiar payloads ni identificadores del cliente."""
import uuid
from django.db import transaction
from django.urls import resolve, Resolver404
from Usuarios.models import AuditEvent

EVENTS = {
    ('api-patient-detail', 'GET'): ('PATIENT_VIEW', 'patient'),
    ('api-patient-detail', 'PUT'): ('PATIENT_UPDATE', 'patient'),
    ('api-patient-detail', 'PATCH'): ('PATIENT_UPDATE', 'patient'),
    ('api-medical-history', 'PUT'): ('CLINICAL_HISTORY_UPDATE', 'patient'),
    ('api-odontogram', 'PUT'): ('ODONTOGRAM_UPDATE', 'patient'),
    ('api-appointment-list', 'POST'): ('APPOINTMENT_CREATE', 'appointment'),
    ('api-appointment-detail', 'PUT'): ('APPOINTMENT_UPDATE', 'appointment'),
    ('api-appointment-detail', 'PATCH'): ('APPOINTMENT_UPDATE', 'appointment'),
    ('api-appointment-complete', 'POST'): ('APPOINTMENT_TRANSITION', 'appointment'),
    ('api-appointment-cancel', 'POST'): ('APPOINTMENT_TRANSITION', 'appointment'),
    ('api-clinical-images', 'POST'): ('CLINICAL_IMAGE_UPLOAD', 'patient'),
    ('api-clinical-image-detail', 'DELETE'): ('CLINICAL_IMAGE_DELETE', 'image'),
    ('api-clinical-image-file', 'GET'): ('CLINICAL_IMAGE_VIEW', 'image'),
    ('api-clinical-image-result-file', 'GET'): ('CLINICAL_IMAGE_VIEW', 'image'),
    ('api-analysis-run-file', 'GET'): ('CLINICAL_IMAGE_VIEW', 'image'),
    ('api-consent', 'GET'): ('CONSENT_VIEW', 'patient'),
    ('api-consent', 'POST'): ('CONSENT_UPDATE', 'patient'),
    ('api-consent-file', 'GET'): ('CONSENT_VIEW', 'patient'),
    ('api-consent-pdf', 'GET'): ('CONSENT_VIEW', 'patient'),
    ('api-export-patients', 'GET'): ('CLINICAL_EXPORT', 'patients'),
    ('api-export-consultations', 'GET'): ('CLINICAL_EXPORT', 'consultations'),
    ('api-export-images', 'GET'): ('CLINICAL_EXPORT', 'images'),
}


class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.request_id = uuid.uuid4()
        try:
            match = resolve(request.path_info)
            event = EVENTS.get((match.url_name, request.method))
        except Resolver404:
            match, event = None, None

        # Writes and their success events commit together. AI invokes expensive
        # external processing, so it is not wrapped in a DB transaction.
        atomic = event and request.method in ('POST', 'PUT', 'PATCH', 'DELETE') and event[0] != 'AI_ANALYSIS_REQUESTED'
        if atomic:
            with transaction.atomic():
                response = self.get_response(request)
                self.record(request, response, match, event)
                if response.status_code >= 400:
                    transaction.set_rollback(True)
        else:
            response = self.get_response(request)
            self.record(request, response, match, event)
        response['X-Request-ID'] = str(request.request_id)
        return response

    @staticmethod
    def record(request, response, match, event):
        auth_event = getattr(request, 'audit_auth_event', None)
        if auth_event and (auth_event[2] == 'failure' or 200 <= response.status_code < 400):
            action, actor, outcome = auth_event
            AuditEvent.objects.create(action=action, actor=actor, outcome=outcome, request_id=request.request_id)
        success = 200 <= response.status_code < 300
        if not event or not success:
            return
        user = request.user if request.user.is_authenticated else None
        if user is None:
            return
        kwargs = match.kwargs
        resource_id = getattr(request, 'audit_resource_id', None) or kwargs.get('patient_id', kwargs.get('paciente_id', kwargs.get('imagen_id', kwargs.get('image_id', kwargs.get('resource_id', kwargs.get('id', kwargs.get('pk', '')))))))
        AuditEvent.objects.create(actor=user, action=event[0], resource_type=event[1], resource_id=str(resource_id), request_id=request.request_id)
