from django.contrib import admin

from .models import CategoriaProducto, Producto


@admin.register(CategoriaProducto)
class CategoriaProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "estado")


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "categoria", "tipo", "precio", "stock_disponible", "estado")
    list_filter = ("tipo", "estado", "categoria")
    search_fields = ("nombre", "descripcion")
