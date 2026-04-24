from django.contrib import admin

from .models import FotoSeguimiento, SeguimientoCliente


@admin.register(SeguimientoCliente)
class SeguimientoClienteAdmin(admin.ModelAdmin):
    list_display = ("cliente", "tipo_interaccion", "estado", "fecha_cita", "tratamiento_aceptado", "usuario")
    list_filter = ("tipo_interaccion", "estado", "tratamiento_aceptado")
    search_fields = ("cliente__nombre_completo", "cliente__telefono", "observacion", "asunto")


@admin.register(FotoSeguimiento)
class FotoSeguimientoAdmin(admin.ModelAdmin):
    list_display = ("cliente", "fecha_envio", "enviado_al_cliente")
    list_filter = ("enviado_al_cliente",)
    search_fields = ("cliente__nombre_completo", "descripcion")
