"""Operator-only recovery after an out-of-band identity and incident review."""
import secrets
import uuid

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from Usuarios.models import AuditEvent, MFACredential, MFAChallenge
from api.authentication import revoke_user_sessions


class Command(BaseCommand):
    help = 'Restablece MFA tras verificación externa del titular; invalida contraseña y sesiones. No envía correo.'

    def add_arguments(self, parser):
        parser.add_argument('username')
        parser.add_argument('--confirm-username', required=True)
        parser.add_argument('--reason', required=True)

    @transaction.atomic
    def handle(self, *args, **options):
        if options['confirm_username'] != options['username'] or len(options['reason'].strip()) < 20:
            raise CommandError('Confirma el usuario exacto y registra una referencia de autorización de al menos 20 caracteres.')
        User = get_user_model()
        user = User.objects.select_for_update().filter(username=options['username'], is_active=True).first()
        if user is None or not user.email or User.objects.filter(email__iexact=user.email).count() != 1:
            raise CommandError('Se requiere una cuenta activa con correo único verificado por operación.')
        # Do not let someone who knows the old password take over enrollment.
        user.set_password(secrets.token_urlsafe(48))
        user.save(update_fields=['password'])
        revoke_user_sessions(user.pk)
        MFAChallenge.objects.filter(user=user, used_at__isnull=True).update(used_at=timezone.now(), enrollment_ciphertext='')
        MFACredential.objects.filter(user=user).delete()
        for token in OutstandingToken.objects.select_for_update().filter(user=user, expires_at__gt=timezone.now()).iterator():
            BlacklistedToken.objects.get_or_create(token=token)
        # The ticket/reason remains with the operator; no personal details copied.
        event = AuditEvent.objects.create(action='MFA_OPERATOR_RESET', resource_type='user', resource_id=str(user.pk), request_id=uuid.uuid4())
        self.stdout.write(f'Referencia de auditoría para asociar a la autorización: {event.request_id}')
        self.stdout.write(self.style.SUCCESS('MFA restablecido; contraseña anterior y sesiones invalidadas. El titular debe usar recuperación de contraseña. Conserva la autorización operativa.'))
