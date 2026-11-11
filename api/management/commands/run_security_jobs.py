import json
import time
from datetime import timedelta
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from Usuarios.models import AuditEvent, FileInspection, OperationalStatus
from api.services.file_inspection import process_one


class Command(BaseCommand):
    help = 'Local audit export, PDF inspection and privacy-preserving operational alerts.'

    def add_arguments(self, parser):
        parser.add_argument('--once', action='store_true')

    def handle(self, *args, **options):
        while True:
            alerts = []
            try:
                call_command('export_audit', limit=100)
            except CommandError:
                alerts.append('audit_export_unavailable')
            for _ in range(5):
                if not process_one():
                    break
            cutoff = timezone.now() - timedelta(minutes=10)
            if AuditEvent.objects.exclude(integrity_seal='').filter(auditdelivery__isnull=True, timestamp__lt=cutoff).exists():
                alerts.append('audit_delivery_delayed')
            if FileInspection.objects.filter(status__in=['PENDING', 'SCANNING', 'ERROR'], created_at__lt=cutoff).exists():
                alerts.append('file_scans_delayed')
            if FileInspection.objects.filter(status='REJECTED').exists():
                alerts.append('file_rejected')
            OperationalStatus.objects.update_or_create(job='security_worker', defaults={'updated_at': timezone.now(), 'healthy': not alerts})
            self.stdout.write(json.dumps({'event': 'security_jobs', 'at': timezone.now().isoformat(), 'alerts': alerts}))
            if options['once']:
                return
            time.sleep(15)
