from django import forms
from django.forms import formset_factory
from django.utils import timezone

from apps.catalogo.models import Producto
from apps.seguimiento.models import SeguimientoCliente
from apps.ventas.models import Pedido
from .models import Cliente, ObservacionCliente


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            "nombre_completo",
            "telefono",
            "estado_contacto",
            "direccion",
            "estado",
        ]
        widgets = {
            "direccion": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
        }
        labels = {
            "nombre_completo": "Nombre del cliente",
            "telefono": "Telefono",
            "estado_contacto": "Estado de contacto",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if "class" not in field.widget.attrs:
                field.widget.attrs["class"] = "form-select" if isinstance(field.widget, forms.Select) else "form-control"

        self.fields["nombre_completo"].required = False


class ObservacionClienteForm(forms.ModelForm):
    class Meta:
        model = ObservacionCliente
        fields = ["texto"]
        labels = {"texto": "Nueva observacion"}
        widgets = {
            "texto": forms.Textarea(
                attrs={
                    "rows": 2,
                    "class": "form-control",
                    "placeholder": "Escribe una observacion para agregarla al historial",
                }
            )
        }


class GestionInicialForm(forms.Form):
    tipo_interaccion = forms.ChoiceField(
        label="Tipo de gestion",
        choices=[("", "Sin gestion inicial")] + list(SeguimientoCliente.TipoInteraccion.choices),
        required=False,
    )
    asunto = forms.CharField(label="Asunto", max_length=150, required=False)
    estado = forms.ChoiceField(
        label="Estado de la gestion",
        choices=SeguimientoCliente.Estado.choices,
        initial=SeguimientoCliente.Estado.PENDIENTE,
        required=False,
    )
    fecha_cita = forms.DateTimeField(
        label="Fecha y hora de la cita",
        required=False,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
    )
    proximo_contacto = forms.DateTimeField(
        label="Proximo seguimiento",
        required=False,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
    )
    tratamiento_aceptado = forms.BooleanField(label="Tratamiento aceptado", required=False)
    fotos_pendientes = forms.BooleanField(label="Fotos pendientes", required=False)
    observacion = forms.CharField(
        label="Observacion",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if "class" not in field.widget.attrs:
                if isinstance(field.widget, forms.CheckboxInput):
                    field.widget.attrs["class"] = "form-check-input"
                else:
                    field.widget.attrs["class"] = "form-select" if isinstance(field.widget, forms.Select) else "form-control"

        min_fecha = timezone.localtime().strftime("%Y-%m-%dT%H:%M")
        self.fields["fecha_cita"].widget.attrs["min"] = min_fecha

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get("tipo_interaccion")
        fecha_cita = cleaned_data.get("fecha_cita")

        if tipo == SeguimientoCliente.TipoInteraccion.CITA:
            if not fecha_cita:
                self.add_error("fecha_cita", "Debes indicar la fecha y hora de la cita.")
            elif fecha_cita < timezone.now():
                self.add_error("fecha_cita", "Las citas solo se pueden agendar desde la fecha y hora actual en adelante.")

        return cleaned_data

    def should_save(self, has_files=False):
        if not self.is_bound:
            return False
        data = self.cleaned_data
        watched_fields = [
            "tipo_interaccion",
            "asunto",
            "fecha_cita",
            "proximo_contacto",
            "tratamiento_aceptado",
            "fotos_pendientes",
            "observacion",
        ]
        return has_files or any(data.get(field) for field in watched_fields)


class CompraClienteRapidaForm(forms.Form):
    producto = forms.ModelChoiceField(
        label="Producto o tratamiento",
        queryset=Producto.objects.none(),
        required=False,
        widget=forms.Select(attrs={"class": "form-select compra-producto"}),
    )
    cantidad = forms.IntegerField(
        label="Cantidad",
        min_value=1,
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control compra-cantidad", "min": "1", "placeholder": "Cantidad"}),
    )
    estado = forms.ChoiceField(
        label="Estado",
        choices=Pedido.Estado.choices,
        initial=Pedido.Estado.PAGADO,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["producto"].queryset = Producto.objects.filter(estado=Producto.Estado.ACTIVO).select_related("categoria")
        self.fields["producto"].empty_label = "Elegir producto"

    def clean(self):
        cleaned_data = super().clean()
        producto = cleaned_data.get("producto")
        cantidad = cleaned_data.get("cantidad")
        tiene_datos = any([producto, cantidad])

        if not tiene_datos:
            cleaned_data["guardar_compra"] = False
            return cleaned_data

        cleaned_data["guardar_compra"] = True
        if not producto:
            self.add_error("producto", "Selecciona un producto.")
        if not cantidad:
            self.add_error("cantidad", "Indica la cantidad.")

        return cleaned_data


CompraClienteRapidaFormSet = formset_factory(
    CompraClienteRapidaForm,
    extra=3,
    can_delete=True,
)
