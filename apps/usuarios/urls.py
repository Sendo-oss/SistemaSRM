from django.urls import path

from .views import UsuarioCreateView, UsuarioListView, UsuarioUpdateView

app_name = "usuarios"

urlpatterns = [
    path("", UsuarioListView.as_view(), name="lista"),
    path("nuevo/", UsuarioCreateView.as_view(), name="crear"),
    path("<int:pk>/editar/", UsuarioUpdateView.as_view(), name="editar"),
]
