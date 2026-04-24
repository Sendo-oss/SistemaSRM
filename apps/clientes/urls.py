from django.urls import path

from .views import ClienteCreateView, ClienteDetailView, ClienteListView, ClienteUpdateView

app_name = "clientes"

urlpatterns = [
    path("", ClienteListView.as_view(), name="lista"),
    path("nuevo/", ClienteCreateView.as_view(), name="crear"),
    path("<int:pk>/", ClienteDetailView.as_view(), name="detalle"),
    path("<int:pk>/editar/", ClienteUpdateView.as_view(), name="editar"),
]

