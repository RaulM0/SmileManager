"""Contact only the stored address of an assigned patient in a live clinic."""
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework import serializers
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView

from .services.clinical_access import lock_authorized_patient
from .services.emails import send_patient_email
from .tenant_patients import TenantClinicalContextMixin
from .throttles import EmailThrottle


class ContactInput(serializers.Serializer):
    asunto = serializers.CharField(max_length=200)
    mensaje = serializers.CharField(max_length=10000)

    def validate(self, values):
        if set(self.initial_data) - set(self.fields):
            raise serializers.ValidationError('Solo se permiten asunto y mensaje.')
        if '\n' in values['asunto'] or '\r' in values['asunto']:
            raise serializers.ValidationError({'asunto': 'El asunto debe ocupar una línea.'})
        return values


class DeliveryUnavailable(APIException):
    status_code = 503
    default_detail = 'No fue posible enviar el correo. Inténtalo de nuevo.'


@method_decorator(never_cache, name='dispatch')
class TenantPatientEmail(TenantClinicalContextMixin, APIView):
    throttle_classes = [EmailThrottle]

    @transaction.atomic
    def post(self, request, patient_id):
        self.lock_context()
        patient = lock_authorized_patient(user=request.user, patient_id=patient_id, clinic_id=self.membership.clinic_id)
        serializer = ContactInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Persist audit before delivery, so an audit failure cannot send a message.
        self.record(patient, 'TENANT_PATIENT_EMAIL_SENT')
        try:
            sent = send_patient_email(patient=patient, user=request.user,
                                      subject=serializer.validated_data['asunto'],
                                      message=serializer.validated_data['mensaje'])
        except Exception as exc:
            raise DeliveryUnavailable() from exc
        if sent != 1:
            raise DeliveryUnavailable()
        return Response({'detail': 'Correo enviado correctamente.'})
