"""Tenant-scoped consent acceptance and protected document access."""
import logging
import os

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from Pacientes.models import Consentimiento
from .policies import consistent_or_404
from .serializers import ConsentSerializer
from .services.clinical_records import ClinicalDataConflict
from .tenant_consultations import patient_for
from .tenant_patients import TenantClinicalContextMixin
from .upload_policy import validate_upload

logger = logging.getLogger(__name__)


class TenantConsentSerializer(ConsentSerializer):
    def get_archivo_ine_url(self, consent):
        return reverse('tenant-consent-file', args=[consent.paciente_id, 'identity']) if consent.archivo_ine else None

    def get_pdf_generado(self, consent):
        return reverse('tenant-consent-file', args=[consent.paciente_id, 'pdf']) if consent.pdf_generado else None


class TenantConsentMixin(TenantClinicalContextMixin):
    def consent_for(self, patient, *, lock=False):
        rows = consistent_or_404(self.request.user, Consentimiento, patient, clinic_id=self.membership.clinic_id)
        if lock:
            rows = rows.select_for_update(of=('self',))
        results = list(rows[:2])
        if len(results) > 1:
            raise ClinicalDataConflict('Los consentimientos duplicados requieren conciliación.')
        return results[0] if results else None


@method_decorator(never_cache, name='dispatch')
class TenantConsent(TenantConsentMixin, APIView):
    def get(self, request, patient_id):
        patient = patient_for(request, self.membership.clinic_id, patient_id)
        consent = self.consent_for(patient) or Consentimiento(paciente=patient, medico=request.user, texto='')
        data = TenantConsentSerializer(consent).data
        self.record(patient, 'TENANT_CONSENT_VIEWED')
        return Response(data)

    def post(self, request, patient_id):
        consent = None
        old_name = None
        new_upload_assigned = False
        try:
            with transaction.atomic():
                self.lock_context()
                if any(field in request.data for field in ('clinic', 'clinic_id', 'medico', 'medico_id', 'paciente', 'paciente_id')):
                    raise ValidationError({'detail': 'La clínica, el médico y el paciente se asignan desde el contexto autorizado.'})
                patient = patient_for(request, self.membership.clinic_id, patient_id, lock=True)
                consent = self.consent_for(patient, lock=True) or Consentimiento(paciente=patient, medico=request.user, texto='')
                old_name = consent.archivo_ine.name if consent.archivo_ine else None
                if consent.fecha_aceptacion:
                    return Response({'detail': 'El consentimiento ya fue aceptado.'}, status=409)
                uploaded = request.FILES.get('archivo_ine')
                if uploaded is None:
                    return Response({'archivo_ine': ['Este archivo es obligatorio.']}, status=400)
                try:
                    validate_upload(uploaded, allow_pdf=True)
                except DjangoValidationError as exc:
                    return Response({'archivo_ine': exc.messages}, status=400)
                text = serializers.CharField(allow_blank=True, max_length=100000).run_validation(request.data.get('texto', ''))
                consent.texto = text
                consent.archivo_ine = uploaded
                new_upload_assigned = True
                consent.fecha_aceptacion = timezone.now()
                consent.save()
                self.record(patient, 'TENANT_CONSENT_ACCEPTED')
                data = TenantConsentSerializer(consent).data
        except Exception:
            if new_upload_assigned and consent is not None and consent.archivo_ine and consent.archivo_ine._committed and consent.archivo_ine.name != old_name:
                try:
                    consent.archivo_ine.delete(save=False)
                except Exception:
                    logger.exception('No fue posible limpiar un archivo de consentimiento después de un error de transacción.')
            raise
        return Response(data)


@method_decorator(never_cache, name='dispatch')
class TenantConsentFile(TenantConsentMixin, APIView):
    def get(self, request, patient_id, kind):
        patient = patient_for(request, self.membership.clinic_id, patient_id)
        consent = self.consent_for(patient)
        if consent is None or kind not in ('identity', 'pdf'):
            return Response({'detail': 'Archivo no disponible.'}, status=404)
        file = consent.archivo_ine if kind == 'identity' else consent.pdf_generado
        if not file:
            return Response({'detail': 'Archivo no disponible.'}, status=404)
        try:
            opened = file.open('rb')
        except FileNotFoundError:
            return Response({'detail': 'Archivo no disponible.'}, status=404)
        try:
            self.record(patient, 'TENANT_CONSENT_FILE_VIEWED')
        except Exception:
            opened.close()
            raise
        response = FileResponse(opened, as_attachment=True, filename=os.path.basename(file.name))
        response['Cache-Control'] = 'private, no-store'
        return response
