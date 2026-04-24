from django.db import models


class Cliente(models.Model):
    class Estado(models.TextChoices):
        ACTIVO = "ACTIVO", "Activo"
        INACTIVO = "INACTIVO", "Inactivo"

    nombre_completo = models.CharField(max_length=180, blank=True)
    identificacion = models.CharField(max_length=20, unique=True, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True)
    ubicacion_cliente = models.CharField(max_length=500, blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    observaciones = models.TextField(blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ACTIVO)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nombre_completo", "telefono"]
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return self.nombre_completo or self.telefono or self.identificacion or f"Cliente {self.pk}"

    @property
    def nombre_mostrado(self):
        return str(self)

    def ubicaciones_lista(self):
        prefetched = getattr(self, "_prefetched_objects_cache", {}).get("ubicaciones")
        if prefetched is not None:
            return list(prefetched)
        return list(self.ubicaciones.all())

    @property
    def total_ubicaciones(self):
        return len(self.ubicaciones_lista())

    @property
    def ubicacion_resumen(self):
        ubicaciones = self.ubicaciones_lista()
        if ubicaciones:
            primera = ubicaciones[0]
            return primera.descripcion or primera.enlace
        return self.ubicacion_cliente or "-"


class UbicacionCliente(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="ubicaciones")
    enlace = models.CharField(max_length=500, blank=True)
    descripcion = models.CharField(max_length=255, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        verbose_name = "Ubicacion del cliente"
        verbose_name_plural = "Ubicaciones del cliente"

    def __str__(self):
        return self.descripcion or self.enlace or f"Ubicacion {self.pk}"

    @property
    def es_enlace(self):
        valor = (self.enlace or "").lower()
        return valor.startswith("http://") or valor.startswith("https://")
