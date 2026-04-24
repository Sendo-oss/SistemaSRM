from decimal import Decimal

from django import forms

from .models import CategoriaProducto, Producto


class CategoriaProductoForm(forms.ModelForm):
    class Meta:
        model = CategoriaProducto
        fields = ["nombre", "descripcion", "estado"]
        widgets = {"descripcion": forms.Textarea(attrs={"rows": 3, "class": "form-control"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if "class" not in field.widget.attrs:
                field.widget.attrs["class"] = "form-select" if isinstance(field.widget, forms.Select) else "form-control"


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ["nombre", "precio", "costo_base", "margen_minimo_porcentaje"]
        labels = {
            "nombre": "Nombre de la crema",
            "precio": "Precio de venta",
            "costo_base": "Costo base",
            "margen_minimo_porcentaje": "Margen minimo deseado (%)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

        self.fields["nombre"].widget.attrs["placeholder"] = "Ejemplo: Crema despigmentante"
        self.fields["precio"].required = False
        self.fields["costo_base"].required = False
        self.fields["margen_minimo_porcentaje"].required = False
        self.fields["precio"].widget.attrs["placeholder"] = "Ejemplo: 25.00"
        self.fields["costo_base"].widget.attrs["placeholder"] = "Ejemplo: 12.50"
        self.fields["margen_minimo_porcentaje"].widget.attrs["placeholder"] = "Ejemplo: 20"

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data["precio"] = cleaned_data.get("precio") if cleaned_data.get("precio") is not None else Decimal("0.00")
        cleaned_data["costo_base"] = cleaned_data.get("costo_base") if cleaned_data.get("costo_base") is not None else Decimal("0.00")
        cleaned_data["margen_minimo_porcentaje"] = (
            cleaned_data.get("margen_minimo_porcentaje")
            if cleaned_data.get("margen_minimo_porcentaje") is not None
            else Decimal("20.00")
        )
        return cleaned_data
