from django.contrib import admin
from .models import EstudioComparativo, Paciente, AntescedentesMedicos, Consulta, ImagenesClinicas, Odontograma, Consentimiento

# Register your models here.

class pacientesAdmin(admin.ModelAdmin):
    readonly_fields = ('created','updated')
    
class antecedentesAdmin(admin.ModelAdmin):
    readonly_fields = ('created','updated')
    
class consultaAdmin(admin.ModelAdmin):
    readonly_fields = ('fecha_consulta',)
    
class imagenesAdmin(admin.ModelAdmin):
    readonly_fields = ('fecha_subida',)
    
class odontogramaAdmin(admin.ModelAdmin):
    readonly_fields = ('created','updated')
    
class EstudioComparativoAdmin(admin.ModelAdmin):
    readonly_fields = ('fecha_creacion','fecha_actualizacion')
    
class ConsentimientoAdmin(admin.ModelAdmin):
    readonly_fields = ('fecha_aceptacion',)
    
admin.site.register(Paciente, pacientesAdmin)
admin.site.register(AntescedentesMedicos, antecedentesAdmin)
admin.site.register(Consulta, consultaAdmin)
admin.site.register(ImagenesClinicas, imagenesAdmin)
admin.site.register(Odontograma, odontogramaAdmin)
admin.site.register(EstudioComparativo, EstudioComparativoAdmin)
admin.site.register(Consentimiento, ConsentimientoAdmin)


