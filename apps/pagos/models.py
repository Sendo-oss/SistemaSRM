from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models


class Pago(models.Model):
    class MetodoPago(models.TextChoices):
        EFECTIVO = "EFECTIVO", "Efectivo"
        TRANSFERENCIA = "TRANSFERENCIA", "Transferencia"
        DEPOSITO = "DEPOSITO", "Deposito"
        TARJETA = "TARJETA", "Tarjeta"

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        APROBADO = "APROBADO", "Aprobado"
        RECHAZADO = "RECHAZADO", "Rechazado"
        ANULADO = "ANULADO", "Anulado"

    pedido = models.ForeignKey("ventas.Pedido", on_delete=models.CASCADE, related_name="pagos")
    metodo_pago = models.CharField(max_length=20, choices=MetodoPago.choices)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    referencia = models.CharField(max_length=120, blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    fecha_pago = models.DateTimeField(auto_now_add=True)
    observaciones = models.TextField(blank=True)

    class Meta:
        ordering = ["-fecha_pago"]
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"

    def __str__(self):
        return f"Pago #{self.pk or 'nuevo'}"

    def clean(self):
        if self.monto <= 0:
            raise ValidationError({"monto": "El monto debe ser mayor a cero."})
        if self.pedido_id and self.estado == self.Estado.APROBADO:
            acumulado = (
                self.pedido.pagos.filter(estado=self.Estado.APROBADO)
                .exclude(pk=self.pk)
                .aggregate(total=models.Sum("monto"))
                .get("total")
                or Decimal("0.00")
            )
            if acumulado + self.monto > self.pedido.total:
                raise ValidationError({"monto": "El pago aprobado supera el total del pedido."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        self.pedido.actualizar_estado_por_pagos()
