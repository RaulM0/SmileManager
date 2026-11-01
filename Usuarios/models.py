from django.db import models
from django.contrib.auth.models import User

class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    clinica_nombre = models.CharField('Nombre de la Clínica', max_length=100, blank=True, null=True)
    telefono = models.CharField('Teléfono', max_length=20, blank=True, null=True)
    direccion = models.CharField('Dirección', max_length=255, blank=True, null=True)
    extra = models.TextField('Notas', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - Perfil"


class AuditEvent(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='audit_events')
    action = models.CharField(max_length=64, db_index=True)
    resource_type = models.CharField(max_length=40, blank=True)
    resource_id = models.CharField(max_length=64, blank=True)
    request_id = models.UUIDField(db_index=True)
    outcome = models.CharField(max_length=16, default='success')

    class Meta:
        ordering = ['-timestamp', '-id']
