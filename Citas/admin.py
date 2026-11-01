from django.contrib import admin
from api.admin_security import ClinicalReadOnlyAdmin
from .models import Cita

# Register your models here.
class CitasAdmin(ClinicalReadOnlyAdmin):
    readonly_fields = ('created','updated')

admin.site.register(Cita, CitasAdmin)
