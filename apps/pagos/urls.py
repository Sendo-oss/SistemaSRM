from django.urls import path

from .views import PagoCreateView, PagoDetailView, PagoListView, PagoUpdateView

app_name = "pagos"

urlpatterns = [
    path("", PagoListView.as_view(), name="lista"),
    path("nuevo/", PagoCreateView.as_view(), name="crear"),
    path("<int:pk>/", PagoDetailView.as_view(), name="detalle"),
    path("<int:pk>/editar/", PagoUpdateView.as_view(), name="editar"),
]

