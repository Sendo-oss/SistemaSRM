from django.contrib import admin

from .models import Promocion


@admin.register(Promocion)
class PromocionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo_promocion", "fecha_inicio", "fecha_fin", "activa")
    list_filter = ("tipo_promocion", "activa")
