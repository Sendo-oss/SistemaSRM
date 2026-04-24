from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class Usuario(AbstractUser):
    class Rol(models.TextChoices):
        ADMINISTRADOR = "ADMINISTRADOR", "Administrador"
        EMPLEADO = "EMPLEADO", "Trabajador"
        CLIENTE = "CLIENTE", "Cliente"

    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.EMPLEADO)
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def es_administrador(self):
        return self.is_superuser or self.rol == self.Rol.ADMINISTRADOR

    @property
    def es_trabajador(self):
        return not self.es_administrador and self.rol == self.Rol.EMPLEADO

    def clean(self):
        super().clean()
        es_admin = self.is_superuser or self.rol == self.Rol.ADMINISTRADOR
        if es_admin:
            administradores = Usuario.objects.filter(models.Q(rol=self.Rol.ADMINISTRADOR) | models.Q(is_superuser=True))
            if self.pk:
                administradores = administradores.exclude(pk=self.pk)
            if administradores.count() >= 2:
                raise ValidationError({"rol": "Solo se permiten dos usuarios con rol de administrador."})

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.rol = self.Rol.ADMINISTRADOR
        self.is_staff = self.es_administrador
        self.full_clean()
        super().save(*args, **kwargs)
