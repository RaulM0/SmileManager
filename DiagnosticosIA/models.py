from django.db import models
from django.conf import settings
from django.db.models import Q

class AIAnalysisRun(models.Model):
    RUNNING = 'RUNNING'
    SUCCEEDED = 'SUCCEEDED'
    FAILED = 'FAILED'
    image = models.ForeignKey('Pacientes.ImagenesClinicas', null=True, on_delete=models.SET_NULL, related_name='analysis_runs')
    image_reference = models.BigIntegerField()
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    requested_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=[(RUNNING, RUNNING), (SUCCEEDED, SUCCEEDED), (FAILED, FAILED)])
    model_name = models.CharField(max_length=80)
    model_version = models.CharField(max_length=64)
    input_hash = models.CharField(max_length=64)
    result_name = models.CharField(max_length=512, blank=True)
    detections = models.JSONField(default=list)
    failure_category = models.CharField(max_length=40, blank=True)
    request_id = models.UUIDField()
    explicit_reanalysis = models.BooleanField(default=False)
    idempotency_key = models.UUIDField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['image'], condition=Q(status='RUNNING'), name='one_running_analysis_per_image'), models.UniqueConstraint(fields=['image', 'requested_by', 'idempotency_key'], name='unique_ai_request_key')]
