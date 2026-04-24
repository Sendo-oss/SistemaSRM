from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.db import models


class CategoriaProducto(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    estado = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Categoria de producto"
        verbose_name_plural = "Categorias de productos"

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    class Tipo(models.TextChoices):
        PRODUCTO = "PRODUCTO", "Producto"
        FORMULACION = "FORMULACION", "Formulacion"
        SERVICIO = "SERVICIO", "Servicio"

    class Estado(models.TextChoices):
        ACTIVO = "ACTIVO", "Activo"
        INACTIVO = "INACTIVO", "Inactivo"

    categoria = models.ForeignKey(CategoriaProducto, on_delete=models.PROTECT, related_name="productos")
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.FORMULACION)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    costo_base = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    margen_minimo_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=20)
    stock_disponible = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ACTIVO)
    observaciones = models.TextField(blank=True)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="productos_creados")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Producto"
        verbose_name_plural = "Productos"

    def __str__(self):
        return self.nombre

    def _quantize(self, value):
        return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def utilidad_actual(self):
        return self._quantize(self.precio - self.costo_base)

    @property
    def rentabilidad_actual_porcentaje(self):
        if self.costo_base <= 0:
            return Decimal("0.00")
        porcentaje = (self.utilidad_actual / self.costo_base) * Decimal("100")
        return self._quantize(porcentaje)

    @property
    def precio_minimo_rentable(self):
        if self.costo_base <= 0:
            return Decimal("0.00")
        precio_objetivo = self.costo_base * (Decimal("1.00") + (self.margen_minimo_porcentaje / Decimal("100")))
        return self._quantize(precio_objetivo)

    @property
    def descuento_maximo_rentable_porcentaje(self):
        if self.precio <= 0:
            return Decimal("0.00")
        precio_minimo = self.precio_minimo_rentable
        if precio_minimo >= self.precio:
            return Decimal("0.00")
        descuento = (Decimal("1.00") - (precio_minimo / self.precio)) * Decimal("100")
        return self._quantize(max(descuento, Decimal("0.00")))
