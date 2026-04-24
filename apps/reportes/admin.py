from django.contrib import admin

from .models import ReporteExportado


@admin.register(ReporteExportado)
class ReporteExportadoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "modulo", "creado_en")
