from django.urls import path

from .views import InventarioListView, MovimientoStockCreateView, MovimientoStockListView

app_name = "inventario"

urlpatterns = [
    path("", InventarioListView.as_view(), name="lista"),
    path("movimientos/", MovimientoStockListView.as_view(), name="movimientos"),
    path("movimientos/nuevo/", MovimientoStockCreateView.as_view(), name="crear_movimiento"),
]
