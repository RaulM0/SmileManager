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
