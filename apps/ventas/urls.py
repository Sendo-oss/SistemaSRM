from django.urls import path

from .views import PedidoCreateView, PedidoDetailView, PedidoListView, PedidoUpdateView

app_name = "ventas"

urlpatterns = [
    path("", PedidoListView.as_view(), name="lista"),
    path("nuevo/", PedidoCreateView.as_view(), name="crear"),
    path("<int:pk>/", PedidoDetailView.as_view(), name="detalle"),
    path("<int:pk>/editar/", PedidoUpdateView.as_view(), name="editar"),
]

