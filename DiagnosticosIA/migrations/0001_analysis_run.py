from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [('Pacientes', '0023_clinical_revisions'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(name='AIAnalysisRun', fields=[
        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        ('requested_at', models.DateTimeField(auto_now_add=True)),
        ('started_at', models.DateTimeField()),
        ('completed_at', models.DateTimeField(blank=True, null=True)),
        ('status', models.CharField(choices=[('RUNNING', 'RUNNING'), ('SUCCEEDED', 'SUCCEEDED'), ('FAILED', 'FAILED')], max_length=12)),
        ('model_name', models.CharField(max_length=80)),
        ('model_version', models.CharField(max_length=64)),
        ('input_hash', models.CharField(max_length=64)),
        ('result_name', models.CharField(blank=True, max_length=512)),
        ('detections', models.JSONField(default=list)),
        ('failure_category', models.CharField(blank=True, max_length=40)),
        ('request_id', models.UUIDField()),
        ('explicit_reanalysis', models.BooleanField(default=False)),
        ('idempotency_key', models.UUIDField(blank=True, null=True)),
        ('image_reference', models.BigIntegerField()),
        ('image', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='analysis_runs', to='Pacientes.imagenesclinicas')),
        ('requested_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
    ], options={'constraints': [models.UniqueConstraint(condition=models.Q(('status', 'RUNNING')), fields=('image',), name='one_running_analysis_per_image'), models.UniqueConstraint(fields=('image', 'requested_by', 'idempotency_key'), name='unique_ai_request_key')]})]
