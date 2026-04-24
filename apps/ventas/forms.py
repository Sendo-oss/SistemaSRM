from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory

from apps.catalogo.models import Producto

from .models import DetallePedido, Pedido


class PedidoForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = ["cliente", "promocion", "estado", "observaciones"]
        widgets = {
            "observaciones": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if "class" not in field.widget.attrs:
                field.widget.attrs["class"] = "form-select" if isinstance(field.widget, forms.Select) else "form-control"


class DetallePedidoForm(forms.ModelForm):
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.filter(estado=Producto.Estado.ACTIVO).select_related("categoria"),
        widget=forms.Select(attrs={"class": "form-select producto-select"}),
    )

    class Meta:
        model = DetallePedido
        fields = ["producto", "cantidad", "precio_unitario"]
        widgets = {
            "cantidad": forms.NumberInput(attrs={"class": "form-control cantidad-input", "min": "1"}),
            "precio_unitario": forms.NumberInput(attrs={"class": "form-control precio-input", "step": "0.01", "min": "0"}),
        }


class BaseDetallePedidoFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        filas_validas = 0
        productos = set()
        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue
            if form.cleaned_data.get("DELETE"):
                continue
            producto = form.cleaned_data.get("producto")
            cantidad = form.cleaned_data.get("cantidad")
            if producto and cantidad:
                filas_validas += 1
                if producto.pk in productos:
                    raise forms.ValidationError("No puedes repetir el mismo producto en el mismo pedido.")
                productos.add(producto.pk)
        if filas_validas == 0:
            raise forms.ValidationError("Debes agregar al menos un producto al pedido.")


DetallePedidoFormSet = inlineformset_factory(
    Pedido,
    DetallePedido,
    form=DetallePedidoForm,
    formset=BaseDetallePedidoFormSet,
    extra=1,
    can_delete=True,
)
