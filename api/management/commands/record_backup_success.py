from django.core.management.base import BaseCommand
from django.utils import timezone
from Usuarios.models import OperationalStatus


class Command(BaseCommand):
    help = 'Record a completed local backup; intended for the backup orchestrator.'

    def handle(self, *args, **options):
        OperationalStatus.objects.update_or_create(job='backup', defaults={'updated_at': timezone.now(), 'healthy': True})
