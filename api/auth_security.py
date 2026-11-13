"""Password-verified MFA challenges and management of the user's own sessions."""
import hmac
import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework import permissions, serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.views import APIView

from Usuarios.models import AuthSession, AuditEvent, MFAChallenge, MFACredential
from .authentication import SessionRefreshToken, requires_mfa
from .services.mfa import challenge_id, enrollment_counter, enrollment_data, recovery_codes, verify_code
from .throttles import AddressThrottle, MFAChallengeThrottle, ReauthenticationThrottle
from .auth_views import _auth_origin_allowed, _set_refresh_cookie
from .serializers import SessionUserSerializer


def audit(request, user, action, outcome='success', resource_id=''):
    AuditEvent.objects.create(actor=user, action=action, outcome=outcome, resource_type='security',
                              resource_id=resource_id, request_id=getattr(request._request, 'request_id', uuid.uuid4()))


def locked_challenge(raw):
    row = get_object_or_404(MFAChallenge, pk=challenge_id(raw))
    user = get_user_model().objects.select_for_update().get(pk=row.user_id)
    row = MFAChallenge.objects.select_for_update().get(pk=row.pk)
    if (not user.is_active or row.used_at or row.attempts >= 5 or row.expires_at <= timezone.now() or
            not hmac.compare_digest(row.credential_hash, user.get_session_auth_hash())):
        raise AuthenticationFailed('Verificación expirada o inválida.')
    return user, row


class ChallengeInput(serializers.Serializer):
    challenge = serializers.CharField(max_length=2048)
    code = serializers.CharField(max_length=128, required=False, default='', write_only=True)


class ChallengeAPIView(APIView):
    def get_authenticate_header(self, request):
        return 'MFA realm="SmileManager"'


@method_decorator(never_cache, name='dispatch')
class MFAStart(ChallengeAPIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = [AddressThrottle, MFAChallengeThrottle]

    @transaction.atomic
    def post(self, request):
        if not _auth_origin_allowed(request):
            return Response({'detail': 'Origen no permitido.'}, status=403)
        data = ChallengeInput(data=request.data)
        data.is_valid(raise_exception=True)
        user, challenge = locked_challenge(data.validated_data['challenge'])
        if not challenge.enrollment_ciphertext or MFACredential.objects.filter(user=user).exists():
            return Response({'detail': 'El segundo factor ya está configurado.'}, status=409)
        return Response(enrollment_data(challenge, user.username))


@method_decorator(never_cache, name='dispatch')
class MFAFinish(ChallengeAPIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = [AddressThrottle, MFAChallengeThrottle]

    @transaction.atomic
    def post(self, request):
        if not _auth_origin_allowed(request):
            return Response({'detail': 'Origen no permitido.'}, status=403)
        data = ChallengeInput(data=request.data)
        data.is_valid(raise_exception=True)
        user, challenge = locked_challenge(data.validated_data['challenge'])
        challenge.attempts += 1
        challenge.save(update_fields=['attempts'])
        codes = None
        device = MFACredential.objects.select_for_update().filter(user=user).first()
        if challenge.enrollment_ciphertext and device is None:
            step = enrollment_counter(challenge.enrollment_ciphertext, data.validated_data['code'])
            valid = step is not None
            if valid:
                codes, hashes = recovery_codes()
                MFACredential.objects.create(user=user, secret_ciphertext=challenge.enrollment_ciphertext,
                                             last_counter=step, recovery_hashes=hashes, enabled_at=timezone.now())
                audit(request, user, 'MFA_ENROLLED')
        else:
            valid = bool(device and not challenge.enrollment_ciphertext and verify_code(device, data.validated_data['code']))
        if not valid:
            audit(request, user, 'MFA_VERIFICATION_FAILED', 'failure')
            return Response({'detail': 'Código inválido o ya utilizado.'}, status=401)
        challenge.used_at = timezone.now()
        challenge.enrollment_ciphertext = ''
        challenge.save(update_fields=['used_at', 'enrollment_ciphertext'])
        refresh = SessionRefreshToken.for_user(user, mfa_verified=True)
        audit(request, user, 'AUTH_LOGIN_SUCCESS')
        response = {'authenticated': True, 'access': str(refresh.access_token), 'user': SessionUserSerializer(user).data}
        if codes is not None:
            response['recovery_codes'] = codes
        return _set_refresh_cookie(Response(response), refresh)


class ReauthInput(serializers.Serializer):
    password = serializers.CharField(max_length=1024, trim_whitespace=False, write_only=True)
    code = serializers.CharField(max_length=128, required=False, default='', allow_blank=True, write_only=True)


class ProfileInput(serializers.Serializer):
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)


@method_decorator(never_cache, name='dispatch')
class Reauthenticate(APIView):
    throttle_classes = [AddressThrottle, ReauthenticationThrottle]

    @transaction.atomic
    def post(self, request):
        data = ReauthInput(data=request.data)
        data.is_valid(raise_exception=True)
        user = get_user_model().objects.select_for_update().get(pk=request.user.pk)
        device = MFACredential.objects.select_for_update().filter(user=user).first()
        valid = user.check_password(data.validated_data['password'])
        if valid and (device or requires_mfa(user)):
            valid = bool(device and verify_code(device, data.validated_data['code']))
        if not valid:
            audit(request, user, 'REAUTHENTICATION_FAILED', 'failure')
            return Response({'detail': 'No fue posible confirmar tu identidad.'}, status=401)
        AuthSession.objects.filter(pk=request.security_session.pk, user=user, revoked_at__isnull=True).update(reauthenticated_at=timezone.now())
        audit(request, user, 'SESSION_REAUTHENTICATED')
        return Response({'detail': 'Identidad confirmada.'})


@method_decorator(never_cache, name='dispatch')
class SessionList(APIView):
    def get(self, request):
        from django.conf import settings
        rows = AuthSession.objects.filter(user=request.user, revoked_at__isnull=True, expires_at__gt=timezone.now(),
                                          last_seen_at__gt=timezone.now() - timedelta(seconds=settings.AUTH_IDLE_SECONDS),
                                          credential_hash=request.user.get_session_auth_hash()).order_by('-created_at')[:100]
        return Response([{'id': str(row.pk), 'created_at': row.created_at, 'last_seen_at': row.last_seen_at,
                          'expires_at': row.expires_at, 'mfa_verified': row.mfa_verified,
                          'current': row.pk == request.security_session.pk} for row in rows])


@method_decorator(never_cache, name='dispatch')
class SessionRevoke(APIView):
    @transaction.atomic
    def post(self, request, session_id):
        user = get_user_model().objects.select_for_update().get(pk=request.user.pk)
        row = get_object_or_404(AuthSession.objects.select_for_update(), pk=session_id, user=user)
        row.revoked_at = timezone.now()
        row.save(update_fields=['revoked_at'])
        audit(request, user, 'SESSION_REVOKED', resource_id=str(row.pk))
        return Response(status=204)


@method_decorator(never_cache, name='dispatch')
class RevokeOtherSessions(APIView):
    @transaction.atomic
    def post(self, request):
        get_user_model().objects.select_for_update().get(pk=request.user.pk)
        AuthSession.objects.filter(user=request.user, revoked_at__isnull=True).exclude(pk=request.security_session.pk).update(revoked_at=timezone.now())
        audit(request, request.user, 'OTHER_SESSIONS_REVOKED')
        return Response(status=204)


@method_decorator(never_cache, name='dispatch')
class OwnProfile(APIView):
    @transaction.atomic
    def patch(self, request):
        fields = ProfileInput(data=request.data)
        fields.is_valid(raise_exception=True)
        values = fields.validated_data
        user = get_user_model().objects.select_for_update().get(pk=request.user.pk)
        user.first_name, user.last_name = values['first_name'], values['last_name']
        user.save(update_fields=['first_name', 'last_name'])
        audit(request, user, 'USER_NAME_UPDATED')
        return Response({'first_name': user.first_name, 'last_name': user.last_name})
