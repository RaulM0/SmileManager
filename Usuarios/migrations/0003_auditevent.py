from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('Usuarios', '0002_perfil_clinica_nombre'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(name='AuditEvent', fields=[
        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True)),
        ('action', models.CharField(db_index=True, max_length=64)),
        ('resource_type', models.CharField(blank=True, max_length=40)),
        ('resource_id', models.CharField(blank=True, max_length=64)),
        ('request_id', models.UUIDField(db_index=True)),
        ('outcome', models.CharField(default='success', max_length=16)),
        ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_events', to=settings.AUTH_USER_MODEL)),
    ], options={'ordering': ['-timestamp', '-id']})]
