from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Usuario


class UsuarioForm(UserCreationForm):
    password1 = forms.CharField(
        label="Contrasena",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    password2 = forms.CharField(
        label="Confirmar contrasena",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = Usuario
        fields = [
            "first_name",
            "last_name",
            "username",
            "telefono",
            "direccion",
            "rol",
            "is_active",
        ]
        labels = {
            "first_name": "Nombres",
            "last_name": "Apellidos",
            "telefono": "Telefono",
            "direccion": "Direccion",
            "rol": "Rol del usuario",
            "is_active": "Usuario activo",
        }
        widgets = {
            "direccion": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if "class" not in field.widget.attrs:
                field.widget.attrs["class"] = "form-select" if isinstance(field.widget, forms.Select) else "form-control"

        self.fields["rol"].choices = [
            (Usuario.Rol.ADMINISTRADOR, "Administrador"),
            (Usuario.Rol.EMPLEADO, "Trabajador"),
        ]


class UsuarioUpdateForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = [
            "first_name",
            "last_name",
            "username",
            "telefono",
            "direccion",
            "rol",
            "is_active",
        ]
        labels = {
            "first_name": "Nombres",
            "last_name": "Apellidos",
            "telefono": "Telefono",
            "direccion": "Direccion",
            "rol": "Rol del usuario",
            "is_active": "Usuario activo",
        }
        widgets = {
            "direccion": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if "class" not in field.widget.attrs:
                field.widget.attrs["class"] = "form-select" if isinstance(field.widget, forms.Select) else "form-control"

        self.fields["rol"].choices = [
            (Usuario.Rol.ADMINISTRADOR, "Administrador"),
            (Usuario.Rol.EMPLEADO, "Trabajador"),
        ]
