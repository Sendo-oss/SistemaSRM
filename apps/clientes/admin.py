from django.contrib import admin

from .models import Cliente, UbicacionCliente


class UbicacionClienteInline(admin.TabularInline):
    model = UbicacionCliente
    extra = 1


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("identificacion", "nombre_completo", "telefono", "total_ubicaciones", "estado")
    search_fields = ("identificacion", "nombre_completo", "telefono", "ubicaciones__enlace", "ubicaciones__descripcion", "direccion")
    list_filter = ("estado",)
    inlines = [UbicacionClienteInline]
