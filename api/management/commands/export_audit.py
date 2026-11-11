import json
import urllib.error
import urllib.request
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from Usuarios.models import AuditDelivery, AuditEvent
from Usuarios.audit_integrity import payload, verify


class Command(BaseCommand):
    help = 'Export sealed undelivered events; failed acknowledgements are safely retried.'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=100)

    def handle(self, *args, **options):
        if not settings.AUDIT_COLLECTOR_URL or not settings.AUDIT_INGEST_TOKEN:
            raise CommandError('Audit collector is not configured.')
        if not 1 <= options['limit'] <= 10000:
            raise CommandError('Invalid batch size.')
        try:
            with urllib.request.urlopen(settings.AUDIT_COLLECTOR_URL.rstrip('/') + '/health', timeout=5) as response:
                if json.loads(response.read(1024)).get('status') != 'ok':
                    raise ValueError('health')
        except (OSError, ValueError, AttributeError):
            raise CommandError('Audit collector unavailable.') from None
        delivered = 0
        for event in AuditEvent.objects.filter(auditdelivery__isnull=True).exclude(integrity_seal='').order_by('pk')[:options['limit']]:
            if not verify(event):
                raise CommandError('Audit integrity check failed.')
            body = json.dumps({'payload': payload(event), 'content_sha256': event.content_sha256,
                               'integrity_seal': event.integrity_seal}).encode()
            request = urllib.request.Request(settings.AUDIT_COLLECTOR_URL.rstrip('/') + '/events', data=body,
                                            headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + settings.AUDIT_INGEST_TOKEN})
            try:
                with urllib.request.urlopen(request, timeout=10) as response:
                    receipt = json.loads(response.read(4096))['receipt']
                if not isinstance(receipt, str) or len(receipt) != 64 or any(c not in '0123456789abcdef' for c in receipt):
                    raise ValueError('receipt')
            except (OSError, ValueError, KeyError):
                raise CommandError('Audit collector unavailable or invalid acknowledgement.') from None
            AuditDelivery.objects.get_or_create(event=event, defaults={'receipt': receipt})
            delivered += 1
        self.stdout.write(f'delivered={delivered}')
