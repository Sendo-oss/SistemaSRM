from django.contrib import admin

from .models import MateriaPrima, MovimientoInventario, MovimientoStock, StockProducto


@admin.register(MateriaPrima)
class MateriaPrimaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "lote", "cantidad_disponible", "unidad_medida", "estado")
    search_fields = ("codigo", "nombre", "lote")
    list_filter = ("estado", "unidad_medida")


@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ("materia_prima", "tipo_movimiento", "cantidad", "fecha_movimiento", "usuario")
    list_filter = ("tipo_movimiento",)


@admin.register(StockProducto)
class StockProductoAdmin(admin.ModelAdmin):
    list_display = ("producto", "ubicacion", "cantidad", "actualizado_en")
    list_filter = ("ubicacion",)
    search_fields = ("producto__nombre",)


@admin.register(MovimientoStock)
class MovimientoStockAdmin(admin.ModelAdmin):
    list_display = ("producto", "tipo_movimiento", "ubicacion_origen", "ubicacion_destino", "cantidad", "fecha_movimiento")
    list_filter = ("tipo_movimiento", "ubicacion_destino")
    search_fields = ("producto__nombre", "observacion")
