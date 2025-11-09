from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Paciente(models.Model):
    nombre = models.CharField(max_length=50)
    appat = models.CharField(max_length=50)
    apmat = models.CharField(max_length=50)
    fecha_nacimiento = models.DateField()
    genero = models.CharField(max_length=1, choices=[('M', 'Masculino'), ('F', 'Femenino')])   
    telefono = models.CharField(max_length=10, unique= True)
    email = models.EmailField(unique=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    estatus = models.CharField(max_length=1, choices=[('A', 'Activo'), ('I', 'Inactivo')], default='A')
    medico = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="pacientes")
    
    class Meta:
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'
        
    def __str__(self):
        return f"{self.nombre} {self.appat}"
    
class AntescedentesMedicos(models.Model):
    id_paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='antecedentes_medicos')
    # Detalles medicos
    tratamiento_medico = models.BooleanField(default=False, verbose_name="¿Está en tratamiento médico?")
    problemas_cardiacos = models.BooleanField(default=False, verbose_name="¿Tiene problemas cardíacos?")
    problemas_coagulacion = models.BooleanField(default=False, verbose_name="¿Tiene problemas de coagulación?")
    epilepsia = models.BooleanField(default=False, verbose_name="Epilepsia/Convulsiones")
    gastritis = models.BooleanField(default=False, verbose_name="Gastritis/Úlceras")
    hipertension = models.BooleanField(default=False, verbose_name="Hipertensión")
    anemia = models.BooleanField(default=False, verbose_name="Anemia")
    embarazo = models.BooleanField(default=False, verbose_name="Embarazo/Sospecha de embarazo")
    alergia_medicamentos = models.BooleanField(default=False, verbose_name="Alergia a algún medicamento")
    alergia_especifica = models.BooleanField(default=False, verbose_name="Alergia específica")
    discapacidad = models.BooleanField(default=False, verbose_name="Discapacidad")
    fuma = models.BooleanField(default=False , verbose_name="¿Fuma?")
    
    # Detalles dentales
    respiracion_bucal = models.BooleanField(default=False, verbose_name="Respiración bucal")
    morder_unas = models.BooleanField(default=False, verbose_name="Morderse las uñas")
    chupar_dedo = models.BooleanField(default=False, verbose_name="Chupar dedo o labios")
    rechinar_dientes = models.BooleanField(default=False, verbose_name="Rechinar los dientes")
    sobremordida_vertical = models.BooleanField(default=False, verbose_name="Sobremordida vertical")
    sobremordida_horizontal = models.BooleanField(default=False, verbose_name="Sobremordida horizontal")
    mordida_cruzada = models.BooleanField(default=False, verbose_name="Mordida cruzada")
    mordida_abierta = models.BooleanField(default=False, verbose_name="Mordida abierta")
    desgaste = models.BooleanField(default=False, verbose_name="Desgaste - Abrasion")
    problemas_atm = models.BooleanField(default=False, verbose_name="Problemas ATM chasquidos")
    consumo_citricos = models.BooleanField(default=False, verbose_name="Consumo frecuente de cítricos")
    sangrado_encias = models.BooleanField(default=False, verbose_name="Sangrado de encías")
    
    # Adicionales
    alergias = models.TextField(blank=True, null=True)
    medicamentos = models.TextField(blank=True, null=True)
    cirugias_previas = models.TextField(blank=True, null=True)
    otros = models.TextField(blank=True, null=True)
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Antecedente Medico'
        verbose_name_plural = 'Antecedentes Medicos'
        ordering = ['-created']
        
    def __str__(self):
        return f"Antecedentes de {self.id_paciente.nombre} {self.id_paciente.appat}"
    
class Consulta(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='consultas')
    fecha_consulta = models.DateTimeField()
    motivo_consulta = models.TextField()
    diagnostico = models.TextField(blank=True, null=True)
    tratamiento = models.TextField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Consulta'
        verbose_name_plural = 'Consultas'
        
    def __str__(self):
        return f"Consulta de {self.paciente.nombre} {self.paciente.appat} el {self.fecha_consulta.strftime('%Y-%m-%d')}"
    
class ImagenesClinicas(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='imagenes_clinicas')
    consulta = models.ForeignKey(Consulta, on_delete=models.CASCADE, related_name='imagenes_clinicas', null=True, blank=True)
    tipo_imagen = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True, null=True)
    imagen = models.ImageField(upload_to='imagenes_clinicas/')
    resultados = models.ImageField(upload_to='resultados/', null=True, blank=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Imagen Clinica'
        verbose_name_plural = 'Imagenes Clinicas'
        
    def __str__(self):
        return f"Imagen clinica de {self.paciente.nombre} {self.paciente.appat} en la consulta del {self.consulta.fecha_consulta.strftime('%Y-%m-%d')}"

# Odontograma
class Odontograma(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='odontogramas')
    dientes_permanentes = models.JSONField(default=dict)
    dientes_deciduos = models.JSONField(default=dict)
    resumen_clinico = models.JSONField(default=dict)
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Odontograma de {self.paceinte.nombre} {self.paceinte.appat}"
    
# Estidio Comparativo Progreso

class EstudioComparativo(models.Model):
    paciente = models.ForeignKey('Paciente', on_delete=models.CASCADE)
    fecha_inicio = models.DateField()
    diagnostico = models.CharField(max_length=255, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    
    # Imágenes ANTES
    antes_oclusal_superior = models.ImageField(upload_to='estudios/antes/', null=True, blank=True)
    antes_lateral_izquierda = models.ImageField(upload_to='estudios/antes/', null=True, blank=True)
    antes_frontal = models.ImageField(upload_to='estudios/antes/', null=True, blank=True)
    antes_lateral_derecha = models.ImageField(upload_to='estudios/antes/', null=True, blank=True)
    antes_oclusal_inferior = models.ImageField(upload_to='estudios/antes/', null=True, blank=True)
    
    # Imágenes DESPUÉS
    despues_perfil = models.ImageField(upload_to='estudios/despues/', null=True, blank=True)
    despues_semiperfil = models.ImageField(upload_to='estudios/despues/', null=True, blank=True)
    despues_retrato_frontal = models.ImageField(upload_to='estudios/despues/', null=True, blank=True)
    despues_retrato_sonrisa = models.ImageField(upload_to='estudios/despues/', null=True, blank=True)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Estudio Comparativo"
        verbose_name_plural = "Estudios Comparativos"
    
    def __str__(self):
        return f"Estudio - {self.paciente.nombre} {self.paciente.appat}"