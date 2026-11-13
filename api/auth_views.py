"""Session, login, refresh and logout HTTP endpoints."""
import logging

from django.contrib.auth import authenticate, get_user_model
from django.conf import settings
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework_simplejwt.exceptions import TokenError
from .authentication import SessionRefreshToken as RefreshToken, lock_session, requires_mfa
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from django.db import transaction
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import AuthenticationFailed

from .serializers import SessionUserSerializer
from .throttles import AddressThrottle, AccountThrottle

logger = logging.getLogger(__name__)


class LoginInputSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=100)
    password = serializers.CharField(trim_whitespace=False, write_only=True)


REFRESH_COOKIE = 'smile_refresh'
REFRESH_COOKIE_PATH = '/api/v1/auth/'


def _auth_origin_allowed(request):
    origin = request.headers.get('Origin')
    if not origin:
        return True
    own_origin = f'{request.scheme}://{request.get_host()}'
    return origin == own_origin or origin in settings.CSRF_TRUSTED_ORIGINS


def _refresh_user(request):
    raw = request.COOKIES.get(REFRESH_COOKIE)
    if not raw:
        return None, None
    try:
        token = RefreshToken(raw)
        user = get_user_model().objects.get(pk=token['user_id'], is_active=True)
        return token, user
    except (TokenError, KeyError, ValueError, get_user_model().DoesNotExist):
        return None, None


def _set_refresh_cookie(response, token):
    response.set_cookie(
        REFRESH_COOKIE, str(token), path=REFRESH_COOKIE_PATH,
        secure=settings.SESSION_COOKIE_SECURE, httponly=True, samesite='Strict',
    )
    response['Cache-Control'] = 'no-store'
    return response


@method_decorator(never_cache, name='dispatch')
class SessionView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = [AddressThrottle]

    def get(self, request):
        if not _auth_origin_allowed(request):
            return Response({'detail': 'Origen no permitido.'}, status=403)
        token, user = _refresh_user(request)
        if user is None:
            return Response({'authenticated': False})
        try:
            with transaction.atomic():
                user = get_user_model().objects.select_for_update().get(pk=user.pk, is_active=True)
                token = RefreshToken(request.COOKIES[REFRESH_COOKIE])
                lock_session(user, token.get('sid'))
                return Response({
                    'authenticated': True,
                    'access': str(token.access_token),
                    'user': SessionUserSerializer(user).data,
                })
        except (TokenError, get_user_model().DoesNotExist, AuthenticationFailed):
            return Response({'authenticated': False})


@method_decorator(never_cache, name='dispatch')
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = [AddressThrottle, AccountThrottle]

    def post(self, request):
        if not _auth_origin_allowed(request):
            return Response({'detail': 'Origen no permitido.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = LoginInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password'],
        )
        if user is None:
            request._request.audit_auth_event = ('AUTH_LOGIN_FAILED', None, 'failure')
            return Response(
                {'detail': 'Usuario o contraseña incorrectos'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Recheck the credential while holding the same row lock used by a
        # password reset: an old-password login cannot mint a post-reset token.
        with transaction.atomic():
            user = get_user_model().objects.select_for_update().filter(pk=user.pk, is_active=True).first()
            if user is None or not user.check_password(serializer.validated_data['password']):
                request._request.audit_auth_event = ('AUTH_LOGIN_FAILED', None, 'failure')
                return Response({'detail': 'Usuario o contraseña incorrectos'}, status=status.HTTP_400_BAD_REQUEST)
            from Usuarios.models import MFACredential
            from .services.mfa import new_challenge
            enrolled = MFACredential.objects.filter(user=user).exists()
            if requires_mfa(user) or enrolled:
                return Response({'authenticated': False, 'mfa_required': True,
                                 'enrollment_required': not enrolled,
                                 'challenge': new_challenge(user, enrollment=not enrolled)})
            refresh = RefreshToken.for_user(user)
        request._request.audit_auth_event = ('AUTH_LOGIN_SUCCESS', user, 'success')
        response = Response({
            'authenticated': True,
            'access': str(refresh.access_token),
            'user': SessionUserSerializer(user).data,
        })
        return _set_refresh_cookie(response, refresh)


@method_decorator(never_cache, name='dispatch')
class RefreshView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = [AddressThrottle]

    def post(self, request):
        if not _auth_origin_allowed(request):
            return Response({'detail': 'Origen no permitido.'}, status=status.HTTP_403_FORBIDDEN)
        token, user = _refresh_user(request)
        if user is None:
            response = Response({'detail': 'Sesión expirada.'}, status=status.HTTP_401_UNAUTHORIZED)
            response.delete_cookie(REFRESH_COOKIE, path=REFRESH_COOKIE_PATH)
            return response
        try:
            with transaction.atomic():
                # Serialize refresh with backoffice deactivation; never mint a
                # token from an is_active value read before the row lock.
                user = get_user_model().objects.select_for_update().get(pk=user.pk, is_active=True)
                session = lock_session(user, token.get('sid'))
                OutstandingToken.objects.select_for_update().get(jti=token['jti'])
                token = RefreshToken(request.COOKIES[REFRESH_COOKIE])
                token.blacklist()
                rotated = RefreshToken.for_user(user, session=session)
        except (TokenError, OutstandingToken.DoesNotExist, get_user_model().DoesNotExist, AuthenticationFailed):
            response = Response({'detail': 'Sesión expirada.'}, status=status.HTTP_401_UNAUTHORIZED)
            response.delete_cookie(REFRESH_COOKIE, path=REFRESH_COOKIE_PATH)
            return response
        return _set_refresh_cookie(Response({'access': str(rotated.access_token)}), rotated)


@method_decorator(never_cache, name='dispatch')
class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        if not _auth_origin_allowed(request):
            return Response({'detail': 'Origen no permitido.'}, status=status.HTTP_403_FORBIDDEN)
        token, user = _refresh_user(request)
        if token:
            try:
                with transaction.atomic():
                    from Usuarios.models import AuthSession
                    get_user_model().objects.select_for_update().get(pk=user.pk)
                    AuthSession.objects.filter(pk=token.get('sid'), user=user).update(revoked_at=timezone.now())
                    OutstandingToken.objects.select_for_update().get(jti=token['jti'])
                    RefreshToken(request.COOKIES[REFRESH_COOKIE]).blacklist()
                    request._request.audit_auth_event = ('AUTH_LOGOUT', user, 'success')
            except (TokenError, OutstandingToken.DoesNotExist):
                pass
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie(REFRESH_COOKIE, path=REFRESH_COOKIE_PATH)
        response['Cache-Control'] = 'no-store'
        return response
