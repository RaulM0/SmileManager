"""Explicit, audited offline management of the platform role."""
import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q

from Usuarios.models import AuditEvent, PlatformAdmin


class Command(BaseCommand):
    help = 'Inspect or change an explicit platform role; dry-run unless --apply is supplied.'

    def add_arguments(self, parser):
        parser.add_argument('--actor-id', required=True, type=int)
        parser.add_argument('--user-id', required=True, type=int)
        parser.add_argument('--action', required=True, choices=['grant', 'revoke'])
        parser.add_argument('--apply', action='store_true')

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        active_ids = list(PlatformAdmin.objects.filter(is_active=True, user__is_active=True).values_list('user_id', flat=True))
        ids = set(active_ids) | {options['actor_id'], options['user_id']}
        users = {user.pk: user for user in User.objects.select_for_update().filter(pk__in=ids).order_by('pk')}
        actor, target = users.get(options['actor_id']), users.get(options['user_id'])
        if actor is None or not actor.is_active or target is None:
            raise CommandError('Actor or target is unavailable.')
        explicit = Permission.objects.filter(content_type__app_label='Usuarios', codename='manage_platform_roles').filter(
            Q(user=actor) | Q(group__user=actor)).exists()
        if not explicit:
            raise CommandError('Actor lacks an explicit platform-role management assignment.')
        roles = list(PlatformAdmin.objects.select_for_update().filter(user_id__in=ids).order_by('user_id'))
        role = next((item for item in roles if item.user_id == target.pk), None)
        active = bool(role and role.is_active)
        desired = options['action'] == 'grant'
        if desired and not target.is_active:
            raise CommandError('An inactive user cannot be granted an active platform role.')
        if active and not desired and target.is_active and not any(
                item.user_id != target.pk and item.is_active and users[item.user_id].is_active for item in roles):
            raise CommandError('At least one active platform administrator must remain.')
        if options['apply'] and active != desired:
            if role is None:
                role = PlatformAdmin(user=target)
            role.is_active = desired
            role.save()
            AuditEvent.objects.create(actor=actor, action='PLATFORM_ROLE_GRANTED' if desired else 'PLATFORM_ROLE_REVOKED',
                                      resource_type='user', resource_id=str(target.pk), request_id=uuid.uuid4())
        self.stdout.write(f"{'APPLY' if options['apply'] else 'DRY RUN'} action={options['action']} target={target.pk} changed={str(active != desired).lower()}")
