from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.utils import timezone


class MateriaPrima(models.Model):
    class Estado(models.TextChoices):
        ACTIVO = "ACTIVO", "Activo"
        BAJO_STOCK = "BAJO_STOCK", "Bajo stock"
        VENCIDO = "VENCIDO", "Vencido"
        INACTIVO = "INACTIVO", "Inactivo"

    proveedor = models.ForeignKey("proveedores.Proveedor", on_delete=models.PROTECT, related_name="materias_primas")
    nombre = models.CharField(max_length=150)
    codigo = models.CharField(max_length=50, unique=True)
    lote = models.CharField(max_length=80)
    fecha_ingreso = models.DateField()
    fecha_vencimiento = models.DateField()
    cantidad_disponible = models.DecimalField(max_digits=10, decimal_places=2)
    stock_minimo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unidad_medida = models.CharField(max_length=20)
    costo = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ACTIVO)
    observaciones = models.TextField(blank=True)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="materias_primas_creadas")

    class Meta:
        ordering = ["nombre", "lote"]
        verbose_name = "Materia prima"
        verbose_name_plural = "Materias primas"

    def __str__(self):
        return f"{self.nombre} ({self.lote})"


class MovimientoInventario(models.Model):
    class TipoMovimiento(models.TextChoices):
        ENTRADA = "ENTRADA", "Entrada"
        SALIDA = "SALIDA", "Salida"
        AJUSTE = "AJUSTE", "Ajuste"

    materia_prima = models.ForeignKey(MateriaPrima, on_delete=models.CASCADE, related_name="movimientos")
    tipo_movimiento = models.CharField(max_length=20, choices=TipoMovimiento.choices)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_movimiento = models.DateTimeField(auto_now_add=True)
    motivo = models.CharField(max_length=255, blank=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="movimientos_inventario")

    class Meta:
        ordering = ["-fecha_movimiento"]
        verbose_name = "Movimiento de inventario"
        verbose_name_plural = "Movimientos de inventario"


class StockProducto(models.Model):
    class Ubicacion(models.TextChoices):
        CASA = "CASA", "Casa"
        LOCAL = "LOCAL", "Local"

    producto = models.ForeignKey("catalogo.Producto", on_delete=models.CASCADE, related_name="stocks_ubicacion")
    ubicacion = models.CharField(max_length=20, choices=Ubicacion.choices)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["producto__nombre", "ubicacion"]
        unique_together = ("producto", "ubicacion")
        verbose_name = "Stock por ubicacion"
        verbose_name_plural = "Stock por ubicacion"

    def __str__(self):
        return f"{self.producto} - {self.get_ubicacion_display()}"


class MovimientoStock(models.Model):
    class TipoMovimiento(models.TextChoices):
        INGRESO = "INGRESO", "Ingreso de mercaderia"
        TRANSFERENCIA = "TRANSFERENCIA", "Traslado entre ubicaciones"

    producto = models.ForeignKey("catalogo.Producto", on_delete=models.CASCADE, related_name="movimientos_stock")
    tipo_movimiento = models.CharField(max_length=20, choices=TipoMovimiento.choices, default=TipoMovimiento.INGRESO)
    ubicacion_origen = models.CharField(max_length=20, choices=StockProducto.Ubicacion.choices, blank=True)
    ubicacion_destino = models.CharField(
        max_length=20,
        choices=StockProducto.Ubicacion.choices,
        default=StockProducto.Ubicacion.CASA,
    )
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    observacion = models.CharField(max_length=255, blank=True)
    fecha_movimiento = models.DateTimeField(default=timezone.now)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="movimientos_stock")
    aplicado = models.BooleanField(default=False, editable=False)

    class Meta:
        ordering = ["-fecha_movimiento"]
        verbose_name = "Movimiento de stock"
        verbose_name_plural = "Movimientos de stock"

    def __str__(self):
        return f"{self.producto} - {self.get_tipo_movimiento_display()}"

    def clean(self):
        if self.cantidad <= 0:
            raise ValidationError({"cantidad": "La cantidad debe ser mayor a cero."})

        if self.tipo_movimiento == self.TipoMovimiento.INGRESO:
            self.ubicacion_origen = ""
            if self.ubicacion_destino != StockProducto.Ubicacion.CASA:
                raise ValidationError({"ubicacion_destino": "La mercaderia nueva debe ingresar primero a casa."})

        if self.tipo_movimiento == self.TipoMovimiento.TRANSFERENCIA:
            if not self.ubicacion_origen:
                raise ValidationError({"ubicacion_origen": "Debes indicar la ubicacion de origen."})
            if self.ubicacion_origen == self.ubicacion_destino:
                raise ValidationError("El origen y el destino no pueden ser iguales.")

            stock_origen = self.obtener_stock(self.ubicacion_origen).cantidad
            if not self.pk and self.cantidad > stock_origen:
                raise ValidationError({"cantidad": "No hay suficiente stock en la ubicacion de origen."})

    def obtener_stock(self, ubicacion):
        stock, _ = StockProducto.objects.get_or_create(
            producto=self.producto,
            ubicacion=ubicacion,
            defaults={"cantidad": 0},
        )
        return stock

    def actualizar_stock_total(self):
        total = self.producto.stocks_ubicacion.aggregate(total=Sum("cantidad")).get("total") or 0
        self.producto.stock_disponible = total
        self.producto.save(update_fields=["stock_disponible"])

    def aplicar_movimiento(self):
        if self.tipo_movimiento == self.TipoMovimiento.INGRESO:
            stock_destino = self.obtener_stock(self.ubicacion_destino)
            stock_destino.cantidad += self.cantidad
            stock_destino.save(update_fields=["cantidad", "actualizado_en"])
        else:
            stock_origen = self.obtener_stock(self.ubicacion_origen)
            stock_destino = self.obtener_stock(self.ubicacion_destino)
            stock_origen.cantidad -= self.cantidad
            stock_destino.cantidad += self.cantidad
            stock_origen.save(update_fields=["cantidad", "actualizado_en"])
            stock_destino.save(update_fields=["cantidad", "actualizado_en"])

        self.actualizar_stock_total()

    def save(self, *args, **kwargs):
        self.full_clean()
        es_nuevo = self.pk is None
        super().save(*args, **kwargs)
        if es_nuevo and not self.aplicado:
            self.aplicar_movimiento()
            self.aplicado = True
            super().save(update_fields=["aplicado"])
