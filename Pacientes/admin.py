from django.contrib import admin
from .models import Paciente, AntescedentesMedicos, Consulta, ImagenesClinicas

# Register your models here.

class pacientesAdmin(admin.ModelAdmin):
    readonly_fields = ('created','updated')
    
class antecedentesAdmin(admin.ModelAdmin):
    readonly_fields = ('created','updated')
    
class consultaAdmin(admin.ModelAdmin):
    readonly_fields = ('fecha_consulta',)
    
class imagenesAdmin(admin.ModelAdmin):
    readonly_fields = ('fecha_subida',)
    
admin.site.register(Paciente, pacientesAdmin)
admin.site.register(AntescedentesMedicos, antecedentesAdmin)
admin.site.register(Consulta, consultaAdmin)
admin.site.register(ImagenesClinicas, imagenesAdmin)


