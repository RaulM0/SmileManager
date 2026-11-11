"""Register original signed documents, keeping operator attestation distinct from signature."""
import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from Pacientes.models import ConsentEvidence, ConsentRevocation, ConsentTemplate, PrivacyNotice
from .tenant_consents import TenantConsentMixin, TenantConsentSerializer
from .tenant_consultations import patient_for
from .upload_policy import validate_upload
from .privacy import template_data, notice_data
from .services.document_integrity import seal, verify, file_digest
from .services.document_payloads import evidence_payload
from .services.file_inspection import queue, require_clean, scan_status

logger = logging.getLogger(__name__)


class EvidenceInput(serializers.Serializer):
    template_id = serializers.IntegerField(min_value=1)
    signer_name = serializers.CharField(max_length=300, min_length=3)
    signer_role = serializers.ChoiceField(choices=['PATIENT', 'REPRESENTATIVE'])
    representative_basis = serializers.CharField(max_length=10000, required=False, allow_blank=True, default='')
    signed_on = serializers.DateField()
    attested = serializers.BooleanField()
    supersedes_id = serializers.IntegerField(min_value=1, required=False)

    def validate(self, data):
        if not data['attested']:
            raise serializers.ValidationError('Confirma la verificación del documento y su correspondencia con la plantilla.')
        if data['signer_role'] == 'REPRESENTATIVE' and len(data['representative_basis'].strip()) < 10:
            raise serializers.ValidationError({'representative_basis': 'Describe la representación y la evidencia que la acredita.'})
        if data['signed_on'] > timezone.localdate():
            raise serializers.ValidationError({'signed_on': 'La fecha no puede ser futura.'})
        return data


def revocation_payload(row):
    return {key: str(getattr(row, key)) for key in ('evidence_id', 'recorded_by_id', 'recorded_name', 'reason', 'created_at')}


def evidence_data(record):
    valid = verify(evidence_payload(record), record.content_sha256, record.integrity_seal)
    template = template_data(record.template)
    if record.template_sha256 != record.template.content_sha256:
        valid = False
    revoked = getattr(record, 'revocation', None)
    if revoked and not verify(revocation_payload(revoked), revoked.content_sha256, revoked.integrity_seal):
        valid = False
    return {'id': record.pk, 'template': template, 'signer_name': record.signer_name,
            'signer_role': record.signer_role, 'representative_basis': record.representative_basis,
            'signed_on': record.signed_on, 'recorded_at': record.recorded_at, 'recorded_name': record.recorded_name,
            'scan_status': scan_status(record.signed_document.name), 'file_sha256': record.file_sha256, 'content_sha256': record.content_sha256,
            'integrity': 'verified' if valid else 'invalid', 'supersedes_id': record.supersedes_id,
            'superseded': hasattr(record, 'replacement'),
            'revoked_at': revoked.created_at if revoked else None, 'revocation_reason': revoked.reason if revoked else None,
            'file_url': reverse('consent-evidence-file', args=[record.patient_id, record.pk])}


@method_decorator(never_cache, name='dispatch')
class TenantEvidence(TenantConsentMixin, APIView):
    def get(self, request, patient_id):
        patient = patient_for(request, self.membership.clinic_id, patient_id)
        legacy = self.consent_for(patient)
        templates = [ConsentTemplate.objects.filter(clinic=self.membership.clinic, kind=kind).order_by('-version').first() for kind in ('CLINICAL', 'PRIVACY')]
        records = ConsentEvidence.objects.filter(patient=patient, clinic=self.membership.clinic).select_related('template', 'revocation', 'replacement').order_by('-recorded_at', '-pk')[:100]
        self.record(patient, 'TENANT_CONSENT_VIEWED')
        return Response({'legacy': TenantConsentSerializer(legacy).data if legacy else None,
                         'templates': [template_data(row) for row in templates if row],
                         'records': [evidence_data(row) for row in records]})

    def post(self, request, patient_id):
        record = None
        try:
            with transaction.atomic():
                self.lock_context()
                patient = patient_for(request, self.membership.clinic_id, patient_id, lock=True)
                data = EvidenceInput(data=request.data)
                data.is_valid(raise_exception=True)
                if any(key in request.data for key in ('texto', 'archivo_ine', 'clinic', 'clinic_id', 'paciente', 'paciente_id', 'medico', 'medico_id')):
                    raise serializers.ValidationError({'detail': 'Usa una plantilla publicada y el documento firmado; no se aceptan campos de propiedad ni el flujo anterior.'})
                template = get_object_or_404(ConsentTemplate, pk=data.validated_data['template_id'], clinic=self.membership.clinic)
                template_data(template)
                latest = ConsentTemplate.objects.filter(clinic=self.membership.clinic, kind=template.kind).order_by('-version').first()
                notice = PrivacyNotice.objects.filter(clinic=self.membership.clinic).order_by('-version').first()
                if notice is None or latest.pk != template.pk or (template.kind == 'PRIVACY' and template.privacy_notice_id != notice.pk):
                    return Response({'detail': 'La plantilla o el aviso se actualizaron. Recarga antes de registrar evidencia.'}, status=409)
                notice_data(notice)
                name = request.user.get_full_name().strip()
                if not name:
                    return Response({'detail': 'Registra tu nombre completo antes de incorporar documentos.'}, status=400)
                uploaded = request.FILES.get('signed_document')
                if uploaded is None:
                    raise serializers.ValidationError({'signed_document': 'Adjunta el documento firmado completo.'})
                try:
                    validate_upload(uploaded, allow_pdf=True)
                except DjangoValidationError as exc:
                    raise serializers.ValidationError({'signed_document': exc.messages}) from None
                supersedes = None
                if data.validated_data.get('supersedes_id'):
                    supersedes = get_object_or_404(ConsentEvidence, pk=data.validated_data['supersedes_id'], patient=patient, clinic=self.membership.clinic, template__kind=template.kind)
                    if hasattr(supersedes, 'replacement') or hasattr(supersedes, 'revocation'):
                        return Response({'detail': 'El documento anterior ya fue sustituido o revocado.'}, status=409)
                    if evidence_data(supersedes)['integrity'] != 'verified':
                        return Response({'detail': 'El documento anterior requiere revisión de integridad.'}, status=409)
                record = ConsentEvidence(clinic=self.membership.clinic, patient=patient, template=template,
                                         template_sha256=template.content_sha256, supersedes=supersedes,
                                         recorded_by=request.user, recorded_name=name, recorded_at=timezone.now(),
                                         signer_name=data.validated_data['signer_name'], signer_role=data.validated_data['signer_role'],
                                         representative_basis=data.validated_data['representative_basis'], signed_on=data.validated_data['signed_on'],
                                         signed_document=uploaded, file_sha256=file_digest(uploaded))
                record.content_sha256, record.integrity_seal = seal(evidence_payload(record))
                record.save()
                if record.signed_document.name.lower().endswith('.pdf'):
                    queue(record.signed_document.name, record.file_sha256)
                self.record(record, 'CONSENT_EVIDENCE_RECORDED', 'consent_evidence')
                return Response(evidence_data(record), status=201)
        except Exception:
            if record is not None and record.signed_document and record.signed_document._committed:
                try:
                    record.signed_document.delete(save=False)
                except Exception:
                    logger.error('No fue posible limpiar un archivo de evidencia tras una transacción fallida.')
            raise


@method_decorator(never_cache, name='dispatch')
class EvidenceFile(TenantConsentMixin, APIView):
    def get(self, request, patient_id, evidence_id):
        patient = patient_for(request, self.membership.clinic_id, patient_id)
        record = get_object_or_404(ConsentEvidence.objects.select_related('template'), pk=evidence_id, patient=patient, clinic=self.membership.clinic)
        if evidence_data(record)['integrity'] != 'verified':
            return Response({'detail': 'El documento requiere una revisión de integridad.'}, status=409)
        try:
            opened = record.signed_document.open('rb')
        except FileNotFoundError:
            return Response({'detail': 'Archivo no disponible.'}, status=404)
        try:
            if file_digest(opened) != record.file_sha256:
                opened.close()
                return Response({'detail': 'El archivo no coincide con la evidencia registrada.'}, status=409)
            require_clean(record.signed_document.name, record.file_sha256)
            self.record(record, 'CONSENT_EVIDENCE_DOWNLOADED', 'consent_evidence')
        except Exception:
            opened.close()
            raise
        response = FileResponse(opened, as_attachment=True, filename=f'Consentimiento_{record.pk}' + ('.pdf' if record.signed_document.name.endswith('.pdf') else ''))
        response['Cache-Control'] = 'private, no-store'
        return response


@method_decorator(never_cache, name='dispatch')
class RevokeEvidence(TenantConsentMixin, APIView):
    @transaction.atomic
    def post(self, request, patient_id, evidence_id):
        self.lock_context()
        patient = patient_for(request, self.membership.clinic_id, patient_id, lock=True)
        record = get_object_or_404(ConsentEvidence, pk=evidence_id, patient=patient, clinic=self.membership.clinic)
        if hasattr(record, 'revocation'):
            return Response({'detail': 'La revocación ya está registrada.'}, status=409)
        reason = serializers.CharField(min_length=10, max_length=10000).run_validation(request.data.get('reason', ''))
        if not request.user.get_full_name().strip():
            return Response({'detail': 'Registra tu nombre completo.'}, status=400)
        row = ConsentRevocation(evidence=record, recorded_by=request.user, recorded_name=request.user.get_full_name().strip(), reason=reason, created_at=timezone.now())
        row.content_sha256, row.integrity_seal = seal(revocation_payload(row))
        row.save()
        self.record(record, 'CONSENT_REVOCATION_RECORDED', 'consent_evidence')
        return Response(evidence_data(record), status=201)
