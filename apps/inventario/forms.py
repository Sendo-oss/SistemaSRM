from django import forms

from .models import MovimientoStock, StockProducto


class MovimientoStockForm(forms.ModelForm):
    class Meta:
        model = MovimientoStock
        fields = [
            "producto",
            "tipo_movimiento",
            "ubicacion_origen",
            "ubicacion_destino",
            "cantidad",
            "fecha_movimiento",
            "observacion",
        ]
        widgets = {
            "fecha_movimiento": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
        }
        labels = {
            "ubicacion_origen": "Origen",
            "ubicacion_destino": "Destino",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if "class" not in field.widget.attrs:
                field.widget.attrs["class"] = "form-select" if isinstance(field.widget, forms.Select) else "form-control"

        self.fields["ubicacion_destino"].initial = StockProducto.Ubicacion.CASA
        self.fields["ubicacion_origen"].required = False
