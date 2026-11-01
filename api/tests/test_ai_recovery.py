from datetime import timedelta
from io import StringIO
import uuid

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from DiagnosticosIA.models import AIAnalysisRun
from Usuarios.models import AuditEvent


class AIRecoveryTests(TestCase):
    def make_run(self, started_at):
        return AIAnalysisRun.objects.create(image_reference=1, started_at=started_at, status=AIAnalysisRun.RUNNING, model_name='test', model_version='a' * 64, input_hash='b' * 64, request_id=uuid.uuid4())

    def test_dry_run_apply_and_recent_run(self):
        old = self.make_run(timezone.now() - timedelta(hours=3))
        recent = self.make_run(timezone.now())
        succeeded = self.make_run(timezone.now() - timedelta(hours=3))
        succeeded.status = AIAnalysisRun.SUCCEEDED
        succeeded.save(update_fields=['status'])
        failed = self.make_run(timezone.now() - timedelta(hours=3))
        failed.status = AIAnalysisRun.FAILED
        failed.save(update_fields=['status'])
        output = StringIO()
        call_command('recover_stale_ai_runs', older_than_minutes=60, stdout=output)
        old.refresh_from_db()
        self.assertEqual(old.status, AIAnalysisRun.RUNNING)
        self.assertIn(f'run={old.pk}', output.getvalue())
        with self.assertRaises(CommandError):
            call_command('recover_stale_ai_runs', older_than_minutes=60, apply=True, stdout=StringIO())
        call_command('recover_stale_ai_runs', older_than_minutes=60, apply=True, workers_stopped=True, stdout=StringIO())
        old.refresh_from_db()
        recent.refresh_from_db()
        succeeded.refresh_from_db()
        failed.refresh_from_db()
        self.assertEqual((old.status, old.failure_category), (AIAnalysisRun.FAILED, 'process_interrupted'))
        self.assertEqual(recent.status, AIAnalysisRun.RUNNING)
        self.assertEqual(succeeded.status, AIAnalysisRun.SUCCEEDED)
        self.assertEqual(failed.status, AIAnalysisRun.FAILED)
        self.assertTrue(AuditEvent.objects.filter(action='AI_ANALYSIS_RECOVERED', resource_id=str(old.pk)).exists())
        call_command('recover_stale_ai_runs', older_than_minutes=60, apply=True, workers_stopped=True, stdout=StringIO())
        self.assertEqual(AuditEvent.objects.filter(action='AI_ANALYSIS_RECOVERED').count(), 1)
