from django import forms

from .models import Promocion


class PromocionForm(forms.ModelForm):
    class Meta:
        model = Promocion
        fields = "__all__"
        labels = {
            "nombre": "Nombre del descuento",
            "producto": "Producto relacionado",
            "porcentaje_descuento": "Descuento porcentual (%)",
            "monto_descuento": "Descuento fijo ($)",
            "condicion_aplicacion": "Condicion para aplicar",
            "activa": "Descuento activo",
        }
        widgets = {
            "fecha_inicio": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "fecha_fin": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "descripcion": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "condicion_aplicacion": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if "class" not in field.widget.attrs:
                if isinstance(field.widget, forms.CheckboxInput):
                    field.widget.attrs["class"] = "form-check-input"
                else:
                    field.widget.attrs["class"] = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
