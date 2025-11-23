from django.contrib import admin
from .models import Cita

# Register your models here.
class CitasAdmin(admin.ModelAdmin):
    readonly_fields = ('created','updated')

admin.site.register(Cita, CitasAdmin)
