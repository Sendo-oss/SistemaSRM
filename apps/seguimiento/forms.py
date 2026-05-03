from django import forms
from django.forms import inlineformset_factory

from apps.catalogo.models import Producto
from apps.ventas.models import Pedido

from .models import FotoSeguimiento, SeguimientoCliente


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(file_item, initial) for file_item in data]
        return [single_file_clean(data, initial)]


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
        self.fields["tratamiento_aceptado"].help_text = "Por defecto inicia en No."
        self.fields["fecha_cita"].widget.attrs["min"] = timezone_min_datetime()

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get("tipo_interaccion")
        fecha_cita = cleaned_data.get("fecha_cita")
        if tipo == SeguimientoCliente.TipoInteraccion.CITA and fecha_cita:
            cleaned_data["fecha_interaccion"] = fecha_cita
            cleaned_data["proximo_contacto"] = cleaned_data.get("proximo_contacto") or fecha_cita
        return cleaned_data


class FotoSeguimientoForm(forms.ModelForm):
    class Meta:
        model = FotoSeguimiento
        fields = ["archivo", "descripcion", "enviado_al_cliente"]
        labels = {
            "archivo": "Imagen o archivo",
            "enviado_al_cliente": "Enviada al cliente",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if "class" not in field.widget.attrs:
                if isinstance(field.widget, forms.CheckboxInput):
                    field.widget.attrs["class"] = "form-check-input"
                else:
                    field.widget.attrs["class"] = "form-select" if isinstance(field.widget, forms.Select) else "form-control"

    def has_changed(self):
        if not super().has_changed():
            return False

        archivo = self.files.get(self.add_prefix("archivo"))
        descripcion = (self.data.get(self.add_prefix("descripcion")) or "").strip()
        if not self.instance.pk and not archivo and not descripcion:
            return False
        return True


class SeguimientoObservacionForm(forms.ModelForm):
    class Meta:
        model = SeguimientoCliente
        fields = ["observacion"]
        widgets = {
            "observacion": forms.Textarea(
                attrs={
                    "rows": 4,
                    "class": "form-control",
                    "placeholder": "Escribe una nota de seguimiento para este cliente",
                }
            ),
        }
        labels = {"observacion": "Observacion"}


class SeguimientoFotoRapidaForm(forms.Form):
    archivos = MultipleFileField(
        label="Fotos o archivos",
        widget=MultipleFileInput(attrs={"class": "form-control", "multiple": True}),
    )
    descripcion = forms.CharField(
        label="Descripcion",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej. Antes del tratamiento"}),
    )
    enviado_al_cliente = forms.BooleanField(
        label="Enviado al cliente",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )


class CompraTratamientoForm(forms.Form):
    producto = forms.ModelChoiceField(
        label="Producto o tratamiento",
        queryset=Producto.objects.none(),
        widget=forms.Select(attrs={"class": "form-select", "data-product-price": "true"}),
    )
    cantidad = forms.IntegerField(
        label="Cantidad",
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
    )
    precio_unitario = forms.DecimalField(
        label="Precio unitario",
        min_value=0,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
    )
    estado = forms.ChoiceField(
        label="Estado",
        choices=Pedido.Estado.choices,
        initial=Pedido.Estado.PAGADO,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    observaciones = forms.CharField(
        label="Observacion de compra",
        required=False,
        widget=forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["producto"].queryset = Producto.objects.filter(estado=Producto.Estado.ACTIVO).select_related("categoria")


def timezone_min_datetime():
    from django.utils import timezone

    return timezone.localtime().strftime("%Y-%m-%dT%H:%M")


FotoSeguimientoFormSet = inlineformset_factory(
    SeguimientoCliente,
    FotoSeguimiento,
    form=FotoSeguimientoForm,
    extra=1,
    can_delete=True,
)
