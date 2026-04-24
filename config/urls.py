from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from apps.usuarios.views import cerrar_sesion

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="auth/login.html",
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("logout/", cerrar_sesion, name="logout"),
    path("", include("apps.dashboard.urls")),
    path("usuarios/", include("apps.usuarios.urls")),
    path("clientes/", include("apps.clientes.urls")),
    path("seguimientos/", include("apps.seguimiento.urls")),
    path("catalogo/", include("apps.catalogo.urls")),
    path("proveedores/", include("apps.proveedores.urls")),
    path("inventario/", include("apps.inventario.urls")),
    path("promociones/", include("apps.promociones.urls")),
    path("ventas/", include("apps.ventas.urls")),
    path("pagos/", include("apps.pagos.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
