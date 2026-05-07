from django.urls import path

from .views import (
    AgendaCitasView,
    AgendaSeguimientoActionView,
    FotoSeguimientoListView,
    SeguimientoCreateView,
    SeguimientoDetailView,
    SeguimientoListView,
    SeguimientoUpdateView,
)

app_name = "seguimiento"

urlpatterns = [
    path("", SeguimientoListView.as_view(), name="lista"),
    path("nuevo/", SeguimientoCreateView.as_view(), name="crear"),
    path("agenda/", AgendaCitasView.as_view(), name="agenda"),
    path("agenda/seguimientos/<int:pk>/", AgendaSeguimientoActionView.as_view(), name="agenda_seguimiento"),
    path("fotos/", FotoSeguimientoListView.as_view(), name="fotos"),
    path("<int:pk>/", SeguimientoDetailView.as_view(), name="detalle"),
    path("<int:pk>/editar/", SeguimientoUpdateView.as_view(), name="editar"),
]
