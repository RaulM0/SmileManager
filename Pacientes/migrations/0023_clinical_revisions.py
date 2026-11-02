from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('Pacientes', '0022_nullable_medical_history'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.AddField(model_name='antescedentesmedicos', name='version', field=models.PositiveIntegerField(default=0)),
        migrations.AddField(model_name='odontograma', name='version', field=models.PositiveIntegerField(default=0)),
        migrations.CreateModel(name='ClinicalRevision', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('resource_type', models.CharField(max_length=32)),
            ('resource_id', models.BigIntegerField()),
            ('version', models.PositiveIntegerField()),
            ('snapshot', models.JSONField()),
            ('created', models.DateTimeField(auto_now_add=True)),
            ('actor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ('patient', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='clinical_revisions', to='Pacientes.paciente')),
        ], options={'constraints': [models.UniqueConstraint(fields=('resource_type', 'resource_id', 'version'), name='unique_clinical_revision')]}),
    ]
