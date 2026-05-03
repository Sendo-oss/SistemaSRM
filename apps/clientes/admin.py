from django.contrib import admin

from .models import Cliente, ObservacionCliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nombre_completo", "telefono", "estado_contacto", "estado", "fecha_registro")
    search_fields = ("nombre_completo", "telefono", "direccion", "observaciones_historial__texto")
    list_filter = ("estado", "estado_contacto")


@admin.register(ObservacionCliente)
class ObservacionClienteAdmin(admin.ModelAdmin):
    list_display = ("cliente", "fecha_registro", "usuario")
    search_fields = ("cliente__nombre_completo", "cliente__telefono", "texto")
    list_filter = ("fecha_registro",)
