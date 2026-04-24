from django.contrib import admin

from .models import Pago


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ("pedido", "metodo_pago", "monto", "estado", "fecha_pago")
    list_filter = ("metodo_pago", "estado")
