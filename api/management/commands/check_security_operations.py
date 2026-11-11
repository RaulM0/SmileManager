import json
from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from Usuarios.models import AuditEvent, FileInspection, OperationalStatus


class Command(BaseCommand):
    help = 'Report operational alerts without clinical data; exit nonzero on active alerts.'

    def handle(self, *args, **options):
        now, alerts = timezone.now(), []
        for job, maximum in [('security_worker', timedelta(minutes=5)), ('backup', timedelta(hours=26))]:
            state = OperationalStatus.objects.filter(job=job).first()
            if not state or state.updated_at < now - maximum:
                alerts.append(job + '_overdue')
            elif not state.healthy:
                alerts.append(job + '_unhealthy')
        if AuditEvent.objects.exclude(integrity_seal='').filter(auditdelivery__isnull=True, timestamp__lt=now - timedelta(minutes=10)).exists():
            alerts.append('audit_delivery_delayed')
        if FileInspection.objects.filter(status__in=['PENDING', 'SCANNING', 'ERROR'], created_at__lt=now - timedelta(minutes=10)).exists():
            alerts.append('file_scans_delayed')
        if FileInspection.objects.filter(status='REJECTED').exists():
            alerts.append('files_rejected')
        if AuditEvent.objects.filter(outcome='failure', timestamp__gte=now - timedelta(minutes=5)).count() >= 20:
            alerts.append('access_failure_burst')
        self.stdout.write(json.dumps({'event': 'security_operations', 'alerts': alerts, 'healthy': not alerts}))
        if alerts:
            raise CommandError('Operational attention required.')
