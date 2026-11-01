import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Creates the isolated browser-test account.'

    def handle(self, *args, **options):
        if os.environ.get('DJANGO_SETTINGS_MODULE') != 'SmileManager.settings_e2e':
            raise CommandError('prepare_e2e only runs with SmileManager.settings_e2e')
        for username in ('e2e_doctor', 'e2e_other_doctor'):
            user, _ = get_user_model().objects.get_or_create(username=username)
            user.set_password('e2e_password_123')
            user.save()
        self.stdout.write(self.style.SUCCESS('E2E accounts ready'))
