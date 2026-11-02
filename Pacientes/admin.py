from django.contrib import admin
from api.admin_security import ClinicalReadOnlyAdmin
from .models import EstudioComparativo, Paciente, AntescedentesMedicos, Consulta, ImagenesClinicas, Odontograma, Consentimiento

# Register your models here.

class pacientesAdmin(ClinicalReadOnlyAdmin):
    readonly_fields = ('created','updated')
    
class antecedentesAdmin(ClinicalReadOnlyAdmin):
    readonly_fields = ('created','updated')
    
class consultaAdmin(ClinicalReadOnlyAdmin):
    readonly_fields = ('fecha_consulta',)
    
class imagenesAdmin(ClinicalReadOnlyAdmin):
    readonly_fields = ('fecha_subida',)
    
class odontogramaAdmin(ClinicalReadOnlyAdmin):
    readonly_fields = ('created','updated')
    
class EstudioComparativoAdmin(ClinicalReadOnlyAdmin):
    readonly_fields = ('fecha_creacion','fecha_actualizacion')
    
class ConsentimientoAdmin(ClinicalReadOnlyAdmin):
    readonly_fields = ('fecha_aceptacion',)
    
admin.site.register(Paciente, pacientesAdmin)
admin.site.register(AntescedentesMedicos, antecedentesAdmin)
admin.site.register(Consulta, consultaAdmin)
admin.site.register(ImagenesClinicas, imagenesAdmin)
admin.site.register(Odontograma, odontogramaAdmin)
admin.site.register(EstudioComparativo, EstudioComparativoAdmin)
admin.site.register(Consentimiento, ConsentimientoAdmin)


