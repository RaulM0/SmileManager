"""Mark abandoned runs only after an operator has stopped all inference workers."""
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from DiagnosticosIA.models import AIAnalysisRun
from Usuarios.models import AuditEvent


class Command(BaseCommand):
    help = 'Inspect old AI runs; recovery requires all inference workers to be stopped.'

    def add_arguments(self, parser):
        parser.add_argument('--older-than-minutes', type=int, required=True)
        parser.add_argument('--apply', action='store_true')
        parser.add_argument('--workers-stopped', action='store_true')

    def handle(self, *args, **options):
        minutes = options['older_than_minutes']
        if minutes < 1:
            raise CommandError('older-than-minutes must be positive.')
        if options['apply'] and not options['workers_stopped']:
            raise CommandError('Stop all inference workers and pass --workers-stopped before applying.')
        now = timezone.now()
        cutoff = now - timedelta(minutes=minutes)
        runs = AIAnalysisRun.objects.filter(status=AIAnalysisRun.RUNNING, started_at__lt=cutoff).order_by('pk')
        candidates = list(runs.values_list('pk', 'started_at'))
        for pk, started_at in candidates:
            if not options['apply']:
                age = int((now - started_at).total_seconds())
                self.stdout.write(f'run={pk} status=RUNNING age_seconds={age}')
                continue
            with transaction.atomic():
                run = AIAnalysisRun.objects.select_for_update().filter(pk=pk, status=AIAnalysisRun.RUNNING, started_at__lt=cutoff).first()
                if run is None:
                    continue
                run.status = AIAnalysisRun.FAILED
                run.failure_category = 'process_interrupted'
                run.completed_at = now
                run.save(update_fields=['status', 'failure_category', 'completed_at'])
                AuditEvent.objects.create(action='AI_ANALYSIS_RECOVERED', resource_type='ai_run', resource_id=str(pk), outcome='failure', request_id=run.request_id)
                self.stdout.write(f'run={pk} status=FAILED')
        self.stdout.write(f"{'APPLY' if options['apply'] else 'DRY RUN'} candidates={len(candidates)}")
