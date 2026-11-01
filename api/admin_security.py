from django.contrib import admin
from django.db import models


class ClinicalReadOnlyAdmin(admin.ModelAdmin):
    """Clinical writes must use application services, even for superusers."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        return tuple(f.name for f in self.model._meta.concrete_fields if not isinstance(f, models.FileField))

    def get_exclude(self, request, obj=None):
        # The default FileField widget links directly to storage.
        return tuple(f.name for f in self.model._meta.concrete_fields if isinstance(f, models.FileField))
