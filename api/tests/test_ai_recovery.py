from datetime import timedelta
from io import StringIO
import uuid

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from DiagnosticosIA.models import AIAnalysisRun
from Usuarios.models import AuditEvent, Clinic


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
        call_command('recover_stale_ai_runs', older_than_minutes=60, all_clinics=True, stdout=output)
        old.refresh_from_db()
        self.assertEqual(old.status, AIAnalysisRun.RUNNING)
        self.assertIn(f'run={old.pk}', output.getvalue())
        with self.assertRaises(CommandError):
            call_command('recover_stale_ai_runs', older_than_minutes=60, all_clinics=True, apply=True, stdout=StringIO())
        call_command('recover_stale_ai_runs', older_than_minutes=60, all_clinics=True, apply=True, workers_stopped=True, stdout=StringIO())
        old.refresh_from_db()
        recent.refresh_from_db()
        succeeded.refresh_from_db()
        failed.refresh_from_db()
        self.assertEqual((old.status, old.failure_category), (AIAnalysisRun.FAILED, 'process_interrupted'))
        self.assertEqual(recent.status, AIAnalysisRun.RUNNING)
        self.assertEqual(succeeded.status, AIAnalysisRun.SUCCEEDED)
        self.assertEqual(failed.status, AIAnalysisRun.FAILED)
        self.assertTrue(AuditEvent.objects.filter(action='AI_ANALYSIS_RECOVERED', resource_id=str(old.pk)).exists())
        call_command('recover_stale_ai_runs', older_than_minutes=60, all_clinics=True, apply=True, workers_stopped=True, stdout=StringIO())
        self.assertEqual(AuditEvent.objects.filter(action='AI_ANALYSIS_RECOVERED').count(), 1)

    def test_clinic_scope_does_not_recover_other_clinics(self):
        a = Clinic.objects.create(name='A', slug='a', status='ACTIVE')
        b = Clinic.objects.create(name='B', slug='b', status='ACTIVE')
        first = self.make_run(timezone.now() - timedelta(hours=3))
        second = self.make_run(timezone.now() - timedelta(hours=3))
        first.clinic, second.clinic = a, b
        first.save(update_fields=['clinic'])
        second.save(update_fields=['clinic'])
        call_command('recover_stale_ai_runs', clinic_id=str(a.pk), older_than_minutes=60,
                     apply=True, workers_stopped=True, stdout=StringIO())
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(first.status, AIAnalysisRun.FAILED)
        self.assertEqual(second.status, AIAnalysisRun.RUNNING)
        self.assertTrue(AuditEvent.objects.filter(action='AI_ANALYSIS_RECOVERED', clinic=a, resource_id=str(first.pk)).exists())
