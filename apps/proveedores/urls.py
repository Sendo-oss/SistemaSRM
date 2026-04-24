from django.urls import path

from .views import ProveedorCreateView, ProveedorDetailView, ProveedorListView, ProveedorUpdateView

app_name = "proveedores"

urlpatterns = [
    path("", ProveedorListView.as_view(), name="lista"),
    path("nuevo/", ProveedorCreateView.as_view(), name="crear"),
    path("<int:pk>/", ProveedorDetailView.as_view(), name="detalle"),
    path("<int:pk>/editar/", ProveedorUpdateView.as_view(), name="editar"),
]

