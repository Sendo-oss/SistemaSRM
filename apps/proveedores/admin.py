from django.contrib import admin

from .models import Proveedor


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ("empresa", "contacto", "telefono", "correo", "estado")
    search_fields = ("empresa", "contacto", "correo")
