"""Explicit closure and append-only correction; no representation of advanced signature."""
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from Pacientes.models import Consulta, ConsultationAddendum, ClinicalRevision, Paciente
from .policies import clinic_clinical_queryset
from .serializers import ConsultationSerializer
from .tenant_patients import TenantClinicalContextMixin
from .services.document_integrity import seal, verify, digest
from .services.document_payloads import consultation_payload, addendum_payload, revision_payload
from .services.mfa import verify_code
from Usuarios.models import MFACredential
from .throttles import AddressThrottle, ReauthenticationThrottle


class AttestationInput(serializers.Serializer):
    password = serializers.CharField(max_length=1024, trim_whitespace=False, write_only=True)
    code = serializers.CharField(max_length=128, required=False, default='', allow_blank=True, write_only=True)
    text = serializers.CharField(max_length=50000, required=False, allow_blank=True)


@method_decorator(never_cache, name='dispatch')
class ConsultationAttestation(TenantClinicalContextMixin, APIView):
    throttle_classes = [AddressThrottle, ReauthenticationThrottle]

    @transaction.atomic
    def post(self, request, consultation_id, operation):
        self.lock_context()
        row = get_object_or_404(clinic_clinical_queryset(request.user, self.membership.clinic_id, Consulta).select_for_update(of=('self',)), pk=consultation_id)
        data = AttestationInput(data=request.data)
        data.is_valid(raise_exception=True)
        user = get_user_model().objects.select_for_update().get(pk=request.user.pk)
        device = MFACredential.objects.select_for_update().filter(user=user).first()
        if not user.check_password(data.validated_data['password']) or (device and not verify_code(device, data.validated_data['code'])):
            self.record(row, 'CLINICAL_ATTESTATION_FAILED', 'consultation', outcome='failure')
            return Response({'detail': 'No fue posible confirmar tu identidad.'}, status=403)
        if not user.get_full_name().strip():
            return Response({'detail': 'Registra el nombre completo del profesional antes de cerrar documentos.'}, status=400)
        if operation == 'close':
            if row.status != 'DRAFT':
                return Response({'detail': 'El documento ya está cerrado o es histórico. Utiliza una adenda.'}, status=409)
            row.author_name = user.get_full_name().strip()
            row.closed_at = timezone.now()
            row.status = 'CLOSED'
            row.content_sha256, row.integrity_seal = seal(consultation_payload(row))
            row.save(update_fields=['author_name', 'closed_at', 'status', 'content_sha256', 'integrity_seal'])
            self.record(row, 'CONSULTATION_CLOSED', 'consultation')
        elif operation == 'addendum':
            if row.status not in ('CLOSED', 'LEGACY') or (row.status == 'CLOSED' and not verify(consultation_payload(row), row.content_sha256, row.integrity_seal)):
                return Response({'detail': 'Solo se permiten adendas sobre documentos cerrados verificados o documentos históricos identificados.'}, status=409)
            text = serializers.CharField(min_length=10, max_length=50000).run_validation(data.validated_data.get('text', ''))
            addendum = ConsultationAddendum(consultation=row, author=user, author_name=user.get_full_name().strip(), text=text, created_at=timezone.now(), base_content_sha256=digest(consultation_payload(row)))
            addendum.content_sha256, addendum.integrity_seal = seal(addendum_payload(addendum))
            addendum.save()
            self.record(row, 'CONSULTATION_ADDENDUM_CREATED', 'consultation')
        else:
            return Response(status=404)
        return Response(ConsultationSerializer(row).data)


@method_decorator(never_cache, name='dispatch')
class ClinicalRevisionList(TenantClinicalContextMixin, APIView):
    def get(self, request, patient_id):
        patient = get_object_or_404(clinic_clinical_queryset(request.user, self.membership.clinic_id, Paciente), pk=patient_id)
        rows = ClinicalRevision.objects.filter(patient=patient, clinic_id=self.membership.clinic_id).order_by('-created', '-pk')[:100]
        data = [{'id': row.pk, 'resource_type': row.resource_type, 'version': row.version,
                 'author_name': row.actor_name or 'Autor histórico no acreditado', 'created_at': row.created,
                 'snapshot': row.snapshot, 'integrity': ('verified' if verify(revision_payload(row), row.content_sha256, row.integrity_seal) else 'invalid') if row.content_sha256 else 'legacy_unsealed'} for row in rows]
        self.record(patient, 'CLINICAL_REVISIONS_VIEWED')
        return Response(data)
