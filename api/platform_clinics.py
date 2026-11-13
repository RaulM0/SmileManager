"""Platform clinic onboarding without automatic access to clinical records."""
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from Usuarios.models import AuditEvent, Clinic, ClinicInvitation, ClinicMembership
from .backoffice import Pagination
from api.permissions import IsPlatformAdmin
from .services.platform_clinics import change_clinic_ai, change_clinic_status, create_clinic, invite_initial_administrator, revoke_initial_invitation
from .features import ai_enabled_for_clinic, ai_globally_enabled
from .tenant_views import deliver_invitation, invitation_delivery_url
from .throttles import EmailThrottle


class ClinicSerializer(serializers.ModelSerializer):
    ai_effective = serializers.SerializerMethodField()
    ai_globally_enabled = serializers.SerializerMethodField()

    class Meta:
        model = Clinic
        fields = ('id', 'name', 'slug', 'status', 'ai_enabled', 'ai_effective', 'ai_globally_enabled', 'created_at', 'updated_at')
        read_only_fields = fields

    def get_ai_effective(self, clinic):
        return ai_enabled_for_clinic(clinic)

    def get_ai_globally_enabled(self, clinic):
        return ai_globally_enabled()


class ClinicCreateInput(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    slug = serializers.SlugField(max_length=150)
    status = serializers.ChoiceField(choices=[Clinic.Status.ACTIVE, Clinic.Status.INACTIVE], default=Clinic.Status.INACTIVE)
    initial_admin_email = serializers.EmailField(max_length=254)


@method_decorator(never_cache, name='dispatch')
class PlatformClinics(APIView):
    permission_classes = [IsPlatformAdmin]
    throttle_classes = [EmailThrottle]

    def get(self, request):
        rows = Clinic.objects.order_by('name', 'pk')
        paginator = Pagination()
        page = paginator.paginate_queryset(rows, request, view=self)
        return paginator.get_paginated_response(ClinicSerializer(page, many=True).data)

    def post(self, request):
        data = ClinicCreateInput(data=request.data)
        data.is_valid(raise_exception=True)
        delivery_url = invitation_delivery_url()
        try:
            with transaction.atomic():
                clinic, invitation, token = create_clinic(actor=request.user, request_id=request._request.request_id,
                                                          **data.validated_data)
                deliver_invitation(invitation, token, delivery_url)
        except IntegrityError as exc:
            name = getattr(getattr(exc.__cause__, 'diag', None), 'constraint_name', '') or ''
            if name.endswith('_slug_key') or 'Usuarios_clinic.slug' in str(exc):
                raise serializers.ValidationError({'slug': ['Este identificador ya está en uso.']}) from exc
            raise
        return Response({**ClinicSerializer(clinic).data, 'initial_admin_invitation_id': str(invitation.pk)}, status=201)


class ClinicStatusInput(serializers.Serializer):
    status = serializers.ChoiceField(choices=Clinic.Status.choices)


@method_decorator(never_cache, name='dispatch')
class PlatformClinicStatus(APIView):
    permission_classes = [IsPlatformAdmin]

    def post(self, request, clinic_id):
        data = ClinicStatusInput(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            clinic = change_clinic_status(actor=request.user, clinic_id=clinic_id, target=data.validated_data['status'],
                                          request_id=request._request.request_id)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'status': exc.messages}) from exc
        return Response(ClinicSerializer(clinic).data)


class ClinicAIInput(serializers.Serializer):
    enabled = serializers.BooleanField()


@method_decorator(never_cache, name='dispatch')
class PlatformClinicAI(APIView):
    permission_classes = [IsPlatformAdmin]

    def post(self, request, clinic_id):
        data = ClinicAIInput(data=request.data)
        data.is_valid(raise_exception=True)
        clinic = change_clinic_ai(
            actor=request.user,
            clinic_id=clinic_id,
            enabled=data.validated_data['enabled'],
            request_id=request._request.request_id,
        )
        return Response(ClinicSerializer(clinic).data)


class InitialAdministratorInput(serializers.Serializer):
    email = serializers.EmailField(max_length=254)


@method_decorator(never_cache, name='dispatch')
class PlatformInitialAdministrator(APIView):
    permission_classes = [IsPlatformAdmin]
    throttle_classes = [EmailThrottle]

    def get(self, request, clinic_id):
        clinic = get_object_or_404(Clinic, pk=clinic_id)
        rows = ClinicInvitation.objects.filter(clinic=clinic, role=ClinicMembership.Role.CLINIC_ADMIN,
                                               status=ClinicInvitation.Status.PENDING).order_by('-created_at', '-pk')
        paginator = Pagination()
        page = paginator.paginate_queryset(rows, request, view=self)
        data = [{'id': str(row.pk), 'email': row.email, 'created_at': row.created_at, 'expires_at': row.expires_at} for row in page]
        AuditEvent.objects.create(actor=request.user, clinic=clinic, action='PLATFORM_INITIAL_ADMIN_INVITATIONS_VIEWED',
                                  resource_type='clinic', resource_id=str(clinic.pk), request_id=request._request.request_id)
        return paginator.get_paginated_response(data)

    def post(self, request, clinic_id):
        data = InitialAdministratorInput(data=request.data)
        data.is_valid(raise_exception=True)
        delivery_url = invitation_delivery_url()
        with transaction.atomic():
            invitation, token = invite_initial_administrator(actor=request.user, clinic_id=clinic_id,
                                                             email=data.validated_data['email'],
                                                             request_id=request._request.request_id)
            deliver_invitation(invitation, token, delivery_url)
        return Response({'detail': 'Invitación enviada.', 'invitation_id': str(invitation.pk)}, status=202)


@method_decorator(never_cache, name='dispatch')
class PlatformInitialAdministratorRevoke(APIView):
    permission_classes = [IsPlatformAdmin]

    def post(self, request, clinic_id, invitation_id):
        revoke_initial_invitation(actor=request.user, clinic_id=clinic_id, invitation_id=invitation_id,
                                  request_id=request._request.request_id)
        return Response(status=204)
