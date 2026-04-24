from django.contrib.auth.mixins import UserPassesTestMixin

from .models import Usuario


class SoloPersonalMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (user.is_superuser or user.rol in {Usuario.Rol.ADMINISTRADOR, Usuario.Rol.EMPLEADO})


class SoloAdministradorMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (user.is_superuser or user.rol == Usuario.Rol.ADMINISTRADOR)
