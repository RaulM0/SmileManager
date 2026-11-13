"""Password recovery primitives; never log tokens, addresses, or credentials."""
import logging
from urllib.parse import urlencode, urlsplit

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.utils import timezone
from django.utils import translation
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from Usuarios.models import AuditEvent

logger = logging.getLogger(__name__)
User = get_user_model()


class InvalidReset(Exception):
    pass


def frontend_base():
    value = settings.FRONTEND_URL.strip().rstrip('/')
    if '\\' in value or any(ord(char) < 33 for char in value):
        raise ValueError('Invalid frontend configuration')
    parsed = urlsplit(value)
    valid_scheme = parsed.scheme == 'https' or (settings.DEBUG and parsed.scheme == 'http')
    if not valid_scheme or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.port == 0:
        raise ValueError('Invalid frontend configuration')
    return value


def request_reset(email, request_id):
    # Account existence is never recorded on the unauthenticated request event.
    AuditEvent.objects.create(action='PASSWORD_RESET_REQUESTED', outcome='requested', request_id=request_id)
    matches = list(User.objects.filter(email__iexact=email).only('id', 'email', 'password', 'last_login', 'is_active')[:2])
    if len(matches) != 1 or not matches[0].is_active or not matches[0].has_usable_password():
        return
    user = matches[0]
    try:
        base = frontend_base()
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        # A fragment is not included in HTTP request paths or proxy access logs.
        link = f'{base}/reset-password#{urlencode({"uid": uid, "token": token})}'
        minutes = max(1, (settings.PASSWORD_RESET_TIMEOUT + 59) // 60)
        text = (f'SmileManager\n\nSe solicitó restablecer tu contraseña.\n'
                f'Abre este enlace para continuar: {link}\n\n'
                f'El enlace vence en {minutes} minutos. Si no solicitaste el cambio, ignora este correo. '
                'El equipo de soporte nunca solicitará tu contraseña.')
        html = render_to_string('api/emails/password_reset.html', {'reset_url': link, 'expiry_minutes': minutes})
        message = EmailMultiAlternatives('Restablecer contraseña de SmileManager', text, settings.DEFAULT_FROM_EMAIL, [user.email])
        message.attach_alternative(html, 'text/html')
        message.send(fail_silently=False)
    except Exception:
        # Do not log the exception: SMTP exceptions can contain addresses and paths.
        logger.warning('Password recovery email could not be delivered; request_id=%s', request_id)


def resolve_uid(uid):
    try:
        raw = force_str(urlsafe_base64_decode(uid))
        if not raw.isdecimal() or len(raw) > 20:
            raise ValueError
        return int(raw)
    except (TypeError, ValueError, UnicodeDecodeError, OverflowError):
        raise InvalidReset from None


@transaction.atomic
def confirm_reset(uid, token, password, request_id):
    user_id = resolve_uid(uid)
    try:
        user = User.objects.select_for_update().get(pk=user_id)
    except User.DoesNotExist:
        raise InvalidReset from None
    if not user.is_active or not user.has_usable_password() or not default_token_generator.check_token(user, token):
        raise InvalidReset
    with translation.override('es'):
        try:
            validate_password(password, user=user)
        except ValidationError as exc:
            raise ValidationError([str(message) for message in exc.messages]) from None
    user.set_password(password)
    user.save(update_fields=['password'])
    from api.authentication import revoke_user_sessions
    revoke_user_sessions(user.pk)
    # Same lock order as refresh and account deactivation: user then token rows.
    for outstanding in OutstandingToken.objects.select_for_update().filter(user=user, expires_at__gt=timezone.now()).iterator():
        BlacklistedToken.objects.get_or_create(token=outstanding)
    AuditEvent.objects.create(action='PASSWORD_RESET_COMPLETED', actor=None, resource_type='user',
                              resource_id=str(user.pk), outcome='success', request_id=request_id)
