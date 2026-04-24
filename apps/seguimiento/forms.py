from django import forms
from django.forms import inlineformset_factory

from .models import FotoSeguimiento, SeguimientoCliente


class SeguimientoClienteForm(forms.ModelForm):
    class Meta:
        model = SeguimientoCliente
        fields = [
            "cliente",
            "tipo_interaccion",
            "asunto",
            "estado",
            "fecha_interaccion",
            "fecha_cita",
            "proximo_contacto",
            "tratamiento_aceptado",
            "observacion",
        ]
        widgets = {
            "fecha_interaccion": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "fecha_cita": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "proximo_contacto": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "observacion": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
        }
        labels = {
            "tipo_interaccion": "Tipo de gestion",
            "fecha_interaccion": "Fecha de contacto",
            "fecha_cita": "Fecha y hora de la cita",
            "proximo_contacto": "Proximo seguimiento",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if "class" not in field.widget.attrs:
                if isinstance(field.widget, forms.CheckboxInput):
                    field.widget.attrs["class"] = "form-check-input"
                else:
                    field.widget.attrs["class"] = "form-select" if isinstance(field.widget, forms.Select) else "form-control"

        self.fields["fecha_cita"].required = False
        self.fields["proximo_contacto"].required = False


class FotoSeguimientoForm(forms.ModelForm):
    class Meta:
        model = FotoSeguimiento
        fields = ["archivo", "descripcion", "fecha_envio", "enviado_al_cliente"]
        widgets = {
            "fecha_envio": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
        }
        labels = {
            "archivo": "Imagen o archivo",
            "fecha_envio": "Fecha de envio",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if "class" not in field.widget.attrs:
                if isinstance(field.widget, forms.CheckboxInput):
                    field.widget.attrs["class"] = "form-check-input"
                else:
                    field.widget.attrs["class"] = "form-select" if isinstance(field.widget, forms.Select) else "form-control"


FotoSeguimientoFormSet = inlineformset_factory(
    SeguimientoCliente,
    FotoSeguimiento,
    form=FotoSeguimientoForm,
    extra=1,
    can_delete=True,
)
