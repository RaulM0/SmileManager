"""Read-only historical consent records and protected document access."""
import os

from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework.response import Response
from rest_framework.views import APIView

from Pacientes.models import Consentimiento
from Pacientes.access import consistent_or_404
from .services.file_inspection import require_clean
from .services.document_integrity import file_digest
from .serializers import ConsentSerializer
from .services.clinical_records import ClinicalDataConflict
from .tenant_consultations import patient_for
from .clinic_context import TenantClinicalContextMixin



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
            require_clean(file.name, file_digest(opened))
            self.record(patient, 'TENANT_CONSENT_FILE_VIEWED')
        except Exception:
            opened.close()
            raise
        response = FileResponse(opened, as_attachment=True, filename=os.path.basename(file.name))
        response['Cache-Control'] = 'private, no-store'
        return response
