from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.utils import timezone


class Pedido(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        PAGADO = "PAGADO", "Pagado"
        EN_PROCESO = "EN_PROCESO", "En proceso"
        ENTREGADO = "ENTREGADO", "Entregado"
        CANCELADO = "CANCELADO", "Cancelado"

    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.PROTECT, related_name="pedidos")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="pedidos_registrados")
    promocion = models.ForeignKey("promociones.Promocion", on_delete=models.SET_NULL, null=True, blank=True, related_name="pedidos")
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    observaciones = models.TextField(blank=True)

    class Meta:
        ordering = ["-fecha_pedido"]
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"

    def __str__(self):
        return f"Pedido #{self.pk}"

    def calcular_descuento_promocion(self, subtotal):
        if not self.promocion or not self.promocion.activa:
            return Decimal("0.00")
        hoy = timezone.localdate()
        if self.promocion.fecha_inicio and self.promocion.fecha_inicio > hoy:
            return Decimal("0.00")
        if self.promocion.fecha_fin and self.promocion.fecha_fin < hoy:
            return Decimal("0.00")
        descuento_porcentaje = (subtotal * self.promocion.porcentaje_descuento) / Decimal("100")
        descuento_fijo = self.promocion.monto_descuento or Decimal("0.00")
        return min(subtotal, descuento_porcentaje + descuento_fijo)

    def recalcular_totales(self, guardar=True):
        subtotal = self.detalles.aggregate(total=Sum("subtotal")).get("total") or Decimal("0.00")
        descuento = self.calcular_descuento_promocion(subtotal)
        self.subtotal = subtotal
        self.descuento = descuento
        self.total = subtotal - descuento
        if guardar and self.pk:
            self.save(update_fields=["subtotal", "descuento", "total"])
        return self.total

    @property
    def monto_pagado(self):
        return self.pagos.filter(estado="APROBADO").aggregate(total=Sum("monto")).get("total") or Decimal("0.00")

    @property
    def saldo_pendiente(self):
        saldo = self.total - self.monto_pagado
        return saldo if saldo > 0 else Decimal("0.00")

    def actualizar_estado_por_pagos(self, guardar=True):
        if self.estado in {self.Estado.CANCELADO, self.Estado.ENTREGADO}:
            return self.estado
        nuevo_estado = self.Estado.PAGADO if self.monto_pagado >= self.total and self.total > 0 else self.Estado.PENDIENTE
        self.estado = nuevo_estado
        if guardar and self.pk:
            self.save(update_fields=["estado"])
        return self.estado


class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey("catalogo.Producto", on_delete=models.PROTECT, related_name="detalles_pedido")
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Detalle de pedido"
        verbose_name_plural = "Detalles de pedido"

    def __str__(self):
        return f"{self.producto} x {self.cantidad}"

    def clean(self):
        if self.cantidad <= 0:
            raise ValidationError({"cantidad": "La cantidad debe ser mayor a cero."})
        if self.precio_unitario < 0:
            raise ValidationError({"precio_unitario": "El precio no puede ser negativo."})

    def save(self, *args, **kwargs):
        self.subtotal = Decimal(self.cantidad) * self.precio_unitario
        self.full_clean()
        super().save(*args, **kwargs)
