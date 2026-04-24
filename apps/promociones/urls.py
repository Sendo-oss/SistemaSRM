from django.urls import path

from .views import PromocionCreateView, PromocionDetailView, PromocionListView, PromocionUpdateView

app_name = "promociones"

urlpatterns = [
    path("", PromocionListView.as_view(), name="lista"),
    path("nuevo/", PromocionCreateView.as_view(), name="crear"),
    path("<int:pk>/", PromocionDetailView.as_view(), name="detalle"),
    path("<int:pk>/editar/", PromocionUpdateView.as_view(), name="editar"),
]

