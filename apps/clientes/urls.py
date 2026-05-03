from django.urls import path

from .views import (
    ClienteCreateView,
    ClienteDetailView,
    ClienteEstadoContactoUpdateView,
    ClienteListView,
    ClienteObservacionCreateView,
    ClienteQuickCreateView,
    ClienteUpdateView,
)

app_name = "clientes"

urlpatterns = [
    path("", ClienteListView.as_view(), name="lista"),
    path("nuevo/", ClienteCreateView.as_view(), name="crear"),
    path("rapido/", ClienteQuickCreateView.as_view(), name="crear_rapido"),
    path("<int:pk>/estado-contacto/", ClienteEstadoContactoUpdateView.as_view(), name="estado_contacto"),
    path("<int:pk>/observaciones/", ClienteObservacionCreateView.as_view(), name="agregar_observacion"),
    path("<int:pk>/", ClienteDetailView.as_view(), name="detalle"),
    path("<int:pk>/editar/", ClienteUpdateView.as_view(), name="editar"),
]

