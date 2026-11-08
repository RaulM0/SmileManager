"""Membership discovery and context validation; no clinical data is returned."""
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from urllib.parse import urlsplit
from rest_framework import serializers
from rest_framework.exceptions import APIException
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from Usuarios.models import Clinic, ClinicMembership
from .tenant_context import resolve_clinic_membership
from .services.memberships import change_membership
from .services.invitations import create_invitation, preview_invitation, preview_registration, register_with_invitation, resolve_invitation, revoke_invitation
from .throttles import EmailThrottle, AddressThrottle


def membership_data(membership):
    return {'id': str(membership.clinic_id), 'name': membership.clinic.name,
            'slug': membership.clinic.slug, 'role': membership.role}


@method_decorator(never_cache, name='dispatch')
class MembershipList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rows = ClinicMembership.objects.select_related('clinic').filter(
            user=request.user, user__is_active=True, status=ClinicMembership.Status.ACTIVE,
            clinic__status=Clinic.Status.ACTIVE,
        ).order_by('clinic__name', 'clinic_id')
        return Response([membership_data(row) for row in rows])


@method_decorator(never_cache, name='dispatch')
class ValidateClinicContext(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(membership_data(resolve_clinic_membership(request.user, request.headers.get('X-Clinic-ID'))))


class MembershipChangeInput(serializers.Serializer):
    role = serializers.ChoiceField(choices=ClinicMembership.Role.choices, required=False)
    status = serializers.ChoiceField(choices=ClinicMembership.Status.choices, required=False)

    def validate(self, data):
        if not data or set(self.initial_data) - {'role', 'status'}:
            raise serializers.ValidationError('Indica solamente el rol o estado que se va a cambiar.')
        return data


@method_decorator(never_cache, name='dispatch')
class MembershipDetail(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, membership_id):
        context = resolve_clinic_membership(request.user, request.headers.get('X-Clinic-ID'))
        data = MembershipChangeInput(data=request.data)
        data.is_valid(raise_exception=True)
        membership = change_membership(actor=request.user, clinic_id=context.clinic_id,
                                       membership_id=membership_id, request_id=request._request.request_id,
                                       role=data.validated_data.get('role'), status=data.validated_data.get('status'))
        return Response({'id': str(membership.pk), 'role': membership.role, 'status': membership.status})


class InvitationInput(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    role = serializers.ChoiceField(choices=ClinicMembership.Role.choices)


class InvitationUnavailable(APIException):
    status_code = 503
    default_detail = 'El servicio de invitaciones no está disponible.'


def invitation_delivery_url():
    url = getattr(settings, 'TENANT_INVITATION_URL', '')
    parts = urlsplit(url)
    if parts.scheme != 'https' or not parts.netloc or parts.query or parts.fragment or parts.username or parts.password:
        raise InvitationUnavailable()
    return url


def deliver_invitation(invitation, token, url):
    delivered = send_mail('Invitación a SmileManager', f'Has recibido una invitación. Abre este enlace para aceptarla o rechazarla:\n{url}#{token}',
                          settings.DEFAULT_FROM_EMAIL, [invitation.email], fail_silently=False)
    if delivered != 1:
        raise InvitationUnavailable()


@method_decorator(never_cache, name='dispatch')
class InvitationCreate(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [EmailThrottle]

    def post(self, request):
        context = resolve_clinic_membership(request.user, request.headers.get('X-Clinic-ID'))
        data = InvitationInput(data=request.data)
        data.is_valid(raise_exception=True)
        url = invitation_delivery_url()
        # Email is delivered before commit; a delivery failure rolls back the token.
        # A later commit failure can make a delivered link invalid, but never grants access.
        with transaction.atomic():
            invitation, token = create_invitation(actor=request.user, clinic_id=context.clinic_id,
                                                  request_id=request._request.request_id, **data.validated_data)
            deliver_invitation(invitation, token, url)
        return Response({'detail': 'Invitación enviada.'}, status=202)


class InvitationResolveInput(serializers.Serializer):
    token = serializers.CharField(max_length=100, trim_whitespace=False, write_only=True)
    action = serializers.ChoiceField(choices=['accept', 'reject'])


class InvitationRegisterInput(serializers.Serializer):
    token = serializers.CharField(max_length=100, trim_whitespace=False, write_only=True)
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=256, min_length=8, trim_whitespace=False, write_only=True)


@method_decorator(never_cache, name='dispatch')
class InvitationRegister(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [AddressThrottle]

    def post(self, request):
        data = InvitationRegisterInput(data=request.data)
        data.is_valid(raise_exception=True)
        register_with_invitation(request_id=request._request.request_id, **data.validated_data)
        return Response({'detail': 'Cuenta creada. Inicia sesión para continuar.'}, status=201)


@method_decorator(never_cache, name='dispatch')
class InvitationRegisterPreview(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [AddressThrottle]

    def post(self, request):
        token = serializers.CharField(max_length=100, trim_whitespace=False).run_validation(request.data.get('token'))
        invitation = preview_registration(token)
        return Response({'clinic': invitation.clinic.name, 'role': invitation.role})


@method_decorator(never_cache, name='dispatch')
class InvitationPreview(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [AddressThrottle]

    def post(self, request):
        token = serializers.CharField(max_length=100, trim_whitespace=False).run_validation(request.data.get('token'))
        invitation = preview_invitation(user=request.user, token=token)
        return Response({'clinic': invitation.clinic.name, 'role': invitation.role, 'expires_at': invitation.expires_at})


@method_decorator(never_cache, name='dispatch')
class InvitationResolve(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [AddressThrottle]

    def post(self, request):
        data = InvitationResolveInput(data=request.data)
        data.is_valid(raise_exception=True)
        resolve_invitation(user=request.user, token=data.validated_data['token'],
                           accept=data.validated_data['action'] == 'accept', request_id=request._request.request_id)
        return Response({'detail': 'Invitación procesada.'})


@method_decorator(never_cache, name='dispatch')
class InvitationRevoke(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, invitation_id):
        context = resolve_clinic_membership(request.user, request.headers.get('X-Clinic-ID'))
        revoke_invitation(actor=request.user, clinic_id=context.clinic_id, invitation_id=invitation_id,
                          request_id=request._request.request_id)
        return Response(status=204)
