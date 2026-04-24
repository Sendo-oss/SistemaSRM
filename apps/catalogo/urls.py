from django.urls import path

from .views import ProductoCreateView, ProductoDetailView, ProductoListView, ProductoUpdateView

app_name = "catalogo"

urlpatterns = [
    path("", ProductoListView.as_view(), name="lista"),
    path("nuevo/", ProductoCreateView.as_view(), name="crear"),
    path("<int:pk>/", ProductoDetailView.as_view(), name="detalle"),
    path("<int:pk>/editar/", ProductoUpdateView.as_view(), name="editar"),
]

