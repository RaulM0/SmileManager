"""Clinic-specific published notices and approved consent templates."""
from django.db import transaction
from django.db.models import Max
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework import permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from Pacientes.models import PrivacyNotice, ConsentTemplate
from Usuarios.models import Clinic, AuditEvent
from Usuarios.clinic_context import require_clinic_capability, lock_clinic_capability, resolve_clinic_membership
from .services.document_integrity import seal, verify
from .services.document_payloads import notice_payload, template_payload
from .throttles import AddressThrottle

NOTICE_FIELDS = (
    'legal_name', 'address', 'privacy_email', 'sensitive_data', 'purposes', 'consent_purposes',
    'arco_procedure', 'revocation_procedure', 'limitation_procedure', 'transfers', 'retention', 'changes_procedure',
)


class NoticeInput(serializers.Serializer):
    legal_name = serializers.CharField(max_length=300)
    address = serializers.CharField(max_length=1000)
    privacy_email = serializers.EmailField()
    sensitive_data = serializers.CharField(max_length=10000)
    purposes = serializers.CharField(max_length=10000)
    consent_purposes = serializers.CharField(max_length=10000)
    arco_procedure = serializers.CharField(max_length=20000)
    revocation_procedure = serializers.CharField(max_length=10000)
    limitation_procedure = serializers.CharField(max_length=10000)
    transfers = serializers.CharField(max_length=10000)
    retention = serializers.CharField(max_length=10000)
    changes_procedure = serializers.CharField(max_length=10000)
    review_confirmed = serializers.BooleanField()

    def validate_review_confirmed(self, value):
        if not value:
            raise serializers.ValidationError('Se requiere la revisión del responsable antes de publicar.')
        return value


class TemplateInput(serializers.Serializer):
    kind = serializers.ChoiceField(choices=['CLINICAL', 'PRIVACY'])
    title = serializers.CharField(max_length=250)
    text = serializers.CharField(min_length=20, max_length=100000)
    review_confirmed = serializers.BooleanField()

    def validate_review_confirmed(self, value):
        if not value:
            raise serializers.ValidationError('Se requiere aprobar el contenido y el procedimiento de evidencia antes de publicar.')
        return value


def notice_data(row):
    if not verify(notice_payload(row), row.content_sha256, row.integrity_seal):
        raise serializers.ValidationError({'detail': 'El aviso requiere una revisión de integridad.'})
    return {'id': row.pk, 'version': row.version, 'published_at': row.published_at, 'body': row.body, 'content_sha256': row.content_sha256}


def template_data(row):
    if row.privacy_notice_id:
        notice_data(row.privacy_notice)
    if not verify(template_payload(row), row.content_sha256, row.integrity_seal):
        raise serializers.ValidationError({'detail': 'La plantilla requiere una revisión de integridad.'})
    return {'id': row.pk, 'kind': row.kind, 'version': row.version, 'title': row.title,
            'text': row.text, 'privacy_notice_id': row.privacy_notice_id, 'content_sha256': row.content_sha256}


@method_decorator(never_cache, name='dispatch')
class ClinicNotice(APIView):
    def get(self, request):
        member = resolve_clinic_membership(request.user, request.headers.get('X-Clinic-ID'))
        row = PrivacyNotice.objects.filter(clinic=member.clinic).order_by('-version').first()
        return Response({'configured': bool(row), 'notice': notice_data(row) if row else None})


@method_decorator(never_cache, name='dispatch')
class PublicNotice(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = [AddressThrottle]

    def get(self, request, clinic_slug):
        # A suspension must not remove the privacy contact for past patients.
        clinic = get_object_or_404(Clinic, slug=clinic_slug)
        row = PrivacyNotice.objects.filter(clinic=clinic).order_by('-version').first()
        return Response({'configured': bool(row), 'notice': notice_data(row) if row else None})


@method_decorator(never_cache, name='dispatch')
class PublishNotice(APIView):
    @transaction.atomic
    def post(self, request):
        member = lock_clinic_capability(request.user, request.headers.get('X-Clinic-ID'), 'clinic.manage')
        data = NoticeInput(data=request.data)
        data.is_valid(raise_exception=True)
        name = request.user.get_full_name().strip()
        if not name:
            return Response({'detail': 'El responsable que publica debe tener nombre completo registrado.'}, status=400)
        version = (PrivacyNotice.objects.filter(clinic=member.clinic).aggregate(value=Max('version'))['value'] or 0) + 1
        row = PrivacyNotice(clinic=member.clinic, version=version, body={key: data.validated_data[key] for key in NOTICE_FIELDS}, approved_by=request.user, approved_name=name)
        row.content_sha256, row.integrity_seal = seal(notice_payload(row))
        row.save()
        AuditEvent.objects.create(clinic=member.clinic, actor=request.user, action='PRIVACY_NOTICE_PUBLISHED', resource_type='privacy_notice', resource_id=str(row.pk), request_id=request._request.request_id)
        return Response(notice_data(row), status=201)


@method_decorator(never_cache, name='dispatch')
class Templates(APIView):
    def get(self, request):
        member = require_clinic_capability(request.user, request.headers.get('X-Clinic-ID'), 'clinic.manage')
        return Response([template_data(row) for row in ConsentTemplate.objects.filter(clinic=member.clinic).order_by('-pk')[:100]])

    @transaction.atomic
    def post(self, request):
        member = lock_clinic_capability(request.user, request.headers.get('X-Clinic-ID'), 'clinic.manage')
        data = TemplateInput(data=request.data)
        data.is_valid(raise_exception=True)
        if not request.user.get_full_name().strip():
            return Response({'detail': 'Registra el nombre completo del responsable que publica.'}, status=400)
        notice = PrivacyNotice.objects.filter(clinic=member.clinic).order_by('-version').first()
        if notice is None:
            return Response({'detail': 'Publica primero el aviso de privacidad de la clínica.'}, status=409)
        notice_data(notice)
        kind = data.validated_data['kind']
        version = (ConsentTemplate.objects.filter(clinic=member.clinic, kind=kind).aggregate(value=Max('version'))['value'] or 0) + 1
        row = ConsentTemplate(clinic=member.clinic, kind=kind, version=version, title=data.validated_data['title'], text=data.validated_data['text'],
                              privacy_notice=notice if kind == 'PRIVACY' else None, approved_by=request.user, approved_name=request.user.get_full_name().strip())
        row.content_sha256, row.integrity_seal = seal(template_payload(row))
        row.save()
        AuditEvent.objects.create(clinic=member.clinic, actor=request.user, action='CONSENT_TEMPLATE_PUBLISHED', resource_type='consent_template', resource_id=str(row.pk), request_id=request._request.request_id)
        return Response(template_data(row), status=201)
