from django.core.management.base import BaseCommand, CommandError
from Usuarios.models import AuditEvent
from Usuarios.audit_integrity import verify


class Command(BaseCommand):
    help = 'Verify seals without retrospectively signing historical events.'

    def handle(self, *args, **options):
        sealed = invalid = 0
        for event in AuditEvent.objects.exclude(integrity_seal='').iterator():
            sealed += 1
            invalid += int(not verify(event))
        historical = AuditEvent.objects.filter(integrity_seal='').count()
        self.stdout.write(f'sealed={sealed} invalid={invalid} historical_unsealed={historical}')
        if invalid:
            raise CommandError('Audit integrity check failed.')
