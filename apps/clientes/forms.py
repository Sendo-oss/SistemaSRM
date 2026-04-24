from django import forms
from django.forms import inlineformset_factory

from .models import Cliente, UbicacionCliente


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            "nombre_completo",
            "identificacion",
            "telefono",
            "direccion",
            "fecha_nacimiento",
            "observaciones",
            "estado",
        ]
        widgets = {
            "fecha_nacimiento": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "observaciones": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "direccion": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
        }
        labels = {
            "nombre_completo": "Nombre del cliente",
            "identificacion": "Cedula o identificacion",
            "telefono": "Telefono",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if "class" not in field.widget.attrs:
                field.widget.attrs["class"] = "form-select" if isinstance(field.widget, forms.Select) else "form-control"

        self.fields["nombre_completo"].required = False
        self.fields["identificacion"].required = False


class UbicacionClienteForm(forms.ModelForm):
    class Meta:
        model = UbicacionCliente
        fields = ["enlace", "descripcion"]
        labels = {
            "enlace": "Ubicacion",
            "descripcion": "Descripcion",
        }
        widgets = {
            "enlace": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://maps.google.com/... o referencia",
                }
            ),
            "descripcion": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Casa, trabajo, familiar, entrega, etc.",
                }
            ),
        }


UbicacionClienteFormSet = inlineformset_factory(
    Cliente,
    UbicacionCliente,
    form=UbicacionClienteForm,
    extra=1,
    can_delete=True,
)
