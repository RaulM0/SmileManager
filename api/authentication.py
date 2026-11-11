"""JWTs are capabilities bound to a live, revocable server-side session."""
import hmac
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

from Usuarios.models import AuthSession, ClinicMembership


def requires_mfa(user):
    from Usuarios.permissions import can_access_backoffice
    return bool(user.is_staff or user.is_superuser or can_access_backoffice(user) or
                ClinicMembership.objects.filter(user=user, role='CLINIC_ADMIN', status='ACTIVE', clinic__status='ACTIVE').exists())


def revoke_user_sessions(user_id):
    AuthSession.objects.filter(user_id=user_id, revoked_at__isnull=True).update(revoked_at=timezone.now())


def lock_session(user, sid, *, touch=True):
    now = timezone.now()
    try:
        session = AuthSession.objects.select_for_update().get(pk=sid, user=user)
    except (AuthSession.DoesNotExist, ValueError, TypeError, ValidationError):
        raise AuthenticationFailed('Sesión expirada. Inicia sesión de nuevo.') from None
    if (session.revoked_at or session.expires_at <= now or
            session.last_seen_at <= now - timedelta(seconds=settings.AUTH_IDLE_SECONDS) or
            not hmac.compare_digest(session.credential_hash, user.get_session_auth_hash()) or
            (requires_mfa(user) and not session.mfa_verified)):
        raise AuthenticationFailed('Sesión expirada. Inicia sesión de nuevo.')
    if touch:
        session.last_seen_at = now
        session.save(update_fields=['last_seen_at'])
    return session


class SessionRefreshToken(RefreshToken):
    @classmethod
    def for_user(cls, user, *, session=None, mfa_verified=False):
        now = timezone.now()
        if session is None:
            session = AuthSession.objects.create(
                user=user, last_seen_at=now, expires_at=now + timedelta(seconds=settings.AUTH_ABSOLUTE_SECONDS),
                credential_hash=user.get_session_auth_hash(), mfa_verified=mfa_verified, reauthenticated_at=now,
            )
        token = super().for_user(user)
        token['sid'] = str(session.pk)
        token['exp'] = min(token['exp'], int(session.expires_at.timestamp()))
        OutstandingToken.objects.filter(jti=token['jti']).update(token=str(token))
        return token


def sensitive_request(request):
    path = request.path
    return request.method not in ('GET', 'HEAD', 'OPTIONS') and (
        '/backoffice/' in path or '/clinics/admin/' in path or
        '/clinics/memberships/' in path or '/clinics/invitations/' in path
        or '/auth/profile/' in path or '/auth/sessions/' in path
    )


class SessionJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        result = super().authenticate(request)
        if result is None:
            return None
        original, token = result
        with transaction.atomic():
            user = get_user_model().objects.select_for_update().get(pk=original.pk)
            if not user.is_active:
                raise AuthenticationFailed('Sesión expirada.')
            session = lock_session(user, token.get('sid'))
            if sensitive_request(request) and session.reauthenticated_at <= timezone.now() - timedelta(seconds=settings.AUTH_REAUTH_SECONDS):
                raise PermissionDenied({'detail': 'Confirma tu identidad para continuar.', 'code': 'reauthentication_required'})
        request.security_session = session
        return user, token
