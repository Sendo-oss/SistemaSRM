from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models


class Promocion(models.Model):
    class TipoPromocion(models.TextChoices):
        FRECUENCIA = "FRECUENCIA", "Cliente frecuente"
        VOLUMEN = "VOLUMEN", "Volumen de compra"
        FECHA_ESPECIAL = "FECHA_ESPECIAL", "Fecha especial"
        INACTIVIDAD = "INACTIVIDAD", "Cliente inactivo"
        PRODUCTO = "PRODUCTO", "Por producto"
        MANUAL = "MANUAL", "Manual"

    nombre = models.CharField(max_length=150)
    producto = models.ForeignKey(
        "catalogo.Producto",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="promociones_descuento",
    )
    descripcion = models.TextField(blank=True)
    tipo_promocion = models.CharField(max_length=20, choices=TipoPromocion.choices, default=TipoPromocion.MANUAL)
    porcentaje_descuento = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    monto_descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    condicion_aplicacion = models.TextField(blank=True)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ["-fecha_inicio", "nombre"]
        verbose_name = "Promocion"
        verbose_name_plural = "Promociones"

    def __str__(self):
        return self.nombre

    @property
    def precio_descuento_aplicado(self):
        if not self.producto:
            return None
        descuento_porcentaje = (self.producto.precio * self.porcentaje_descuento) / Decimal("100")
        precio_final = self.producto.precio - descuento_porcentaje - (self.monto_descuento or Decimal("0.00"))
        return max(precio_final, Decimal("0.00"))

    @property
    def ganancia_estimada(self):
        if not self.producto:
            return None
        return self.precio_descuento_aplicado - self.producto.costo_base

    @property
    def es_rentable(self):
        if not self.producto:
            return None
        return self.precio_descuento_aplicado >= self.producto.precio_minimo_rentable

    def clean(self):
        super().clean()

        if self.fecha_fin and self.fecha_inicio and self.fecha_fin < self.fecha_inicio:
            raise ValidationError({"fecha_fin": "La fecha fin no puede ser anterior a la fecha de inicio."})

        if self.producto:
            if self.porcentaje_descuento < 0:
                raise ValidationError({"porcentaje_descuento": "El descuento porcentual no puede ser negativo."})

            if self.monto_descuento < 0:
                raise ValidationError({"monto_descuento": "El descuento fijo no puede ser negativo."})

            if self.precio_descuento_aplicado < self.producto.precio_minimo_rentable:
                raise ValidationError(
                    {
                        "porcentaje_descuento": (
                            f"Este descuento afecta la rentabilidad del producto. "
                            f"El precio minimo rentable es ${self.producto.precio_minimo_rentable}."
                        )
                    }
                )
