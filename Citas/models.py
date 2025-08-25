from django.db import models
from Pacientes.models import Paciente

# Create your models here.

class Cita(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    fecha = models.DateField()
    hora = models.TimeField()
    motivo = models.TextField()
    estatus = models.CharField(max_length=1, choices=[('P', 'Pendiente'), ('C', 'Completada'), ('A', 'Anulada')], default='P')
    observaciones = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Cita'
        verbose_name_plural = 'Citas'
        
    def __str__(self):
        return f'Cita de {self.paciente.nombre} el {self.fecha} a las {self.hora}'