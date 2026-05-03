from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


def ruta_foto_seguimiento(instance, filename):
    nombre_archivo = Path(filename).name
    seguimiento = instance.seguimiento
    if seguimiento.carpeta_tratamiento:
        return f"{seguimiento.carpeta_tratamiento}/{nombre_archivo}"
    return f"seguimientos/cliente_{seguimiento.cliente_id}/{timezone.now():%Y/%m/%d}/{nombre_archivo}"


class SeguimientoCliente(models.Model):
    class TipoInteraccion(models.TextChoices):
        LLAMADA = "LLAMADA", "Llamada"
        CITA = "CITA", "Cita"
        ENVIO_FOTOS = "ENVIO_FOTOS", "Envio de fotos"
        FOTOS_PENDIENTES = "FOTOS_PENDIENTES", "Fotos pendientes"
        SEGUIMIENTO = "SEGUIMIENTO", "Seguimiento"

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        AGENDADO = "AGENDADO", "Agendado"
        EN_PROCESO = "EN_PROCESO", "En proceso"
        COMPLETADO = "COMPLETADO", "Completado"
        CANCELADO = "CANCELADO", "Cancelado"

    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.CASCADE, related_name="seguimientos")
    tipo_interaccion = models.CharField(
        max_length=20,
        choices=TipoInteraccion.choices,
        default=TipoInteraccion.SEGUIMIENTO,
    )
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    asunto = models.CharField(max_length=150, blank=True)
    observacion = models.TextField(blank=True)
    fecha_interaccion = models.DateTimeField(default=timezone.now)
    fecha_cita = models.DateTimeField(null=True, blank=True)
    proximo_contacto = models.DateTimeField(null=True, blank=True)
    tratamiento_aceptado = models.BooleanField(default=False)
    fecha_aceptacion = models.DateTimeField(null=True, blank=True)
    carpeta_tratamiento = models.CharField(max_length=255, blank=True, editable=False)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="seguimientos_registrados",
    )

    class Meta:
        ordering = ["-fecha_cita", "-fecha_interaccion"]
        verbose_name = "Seguimiento de cliente"
        verbose_name_plural = "Seguimientos de clientes"

    def __str__(self):
        return f"{self.cliente} - {self.get_tipo_interaccion_display()}"

    def clean(self):
        if self.tipo_interaccion == self.TipoInteraccion.CITA and not self.fecha_cita:
            raise ValidationError({"fecha_cita": "Debes indicar la fecha y hora de la cita."})
        if self.tipo_interaccion == self.TipoInteraccion.CITA and self.fecha_cita and self.fecha_cita < timezone.now():
            raise ValidationError({"fecha_cita": "Las citas solo se pueden agendar desde la fecha y hora actual en adelante."})

    @property
    def es_pendiente(self):
        return self.estado in {self.Estado.PENDIENTE, self.Estado.AGENDADO, self.Estado.EN_PROCESO}

    @property
    def fecha_referencia(self):
        return self.fecha_cita or self.proximo_contacto or self.fecha_interaccion

    def crear_carpeta_tratamiento(self):
        marca_tiempo = (self.fecha_aceptacion or timezone.now()).strftime("%Y%m%d_%H%M%S")
        cliente_slug = slugify(self.cliente.nombre_mostrado) or f"cliente-{self.cliente_id}"
        carpeta_relativa = f"tratamientos/{cliente_slug}_{self.cliente_id}/{marca_tiempo}"
        carpeta_absoluta = Path(settings.MEDIA_ROOT) / carpeta_relativa
        carpeta_absoluta.mkdir(parents=True, exist_ok=True)
        self.carpeta_tratamiento = carpeta_relativa

    def save(self, *args, **kwargs):
        if self.tratamiento_aceptado and not self.fecha_aceptacion:
            self.fecha_aceptacion = timezone.now()

        if self.tratamiento_aceptado and not self.carpeta_tratamiento:
            self.crear_carpeta_tratamiento()

        if self.tipo_interaccion == self.TipoInteraccion.CITA and self.estado == self.Estado.PENDIENTE:
            self.estado = self.Estado.AGENDADO

        if self.tipo_interaccion == self.TipoInteraccion.CITA and self.fecha_cita:
            self.fecha_interaccion = self.fecha_cita
            if not self.proximo_contacto:
                self.proximo_contacto = self.fecha_cita

        super().save(*args, **kwargs)


class FotoSeguimiento(models.Model):
    seguimiento = models.ForeignKey(SeguimientoCliente, on_delete=models.CASCADE, related_name="fotos")
    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.CASCADE, related_name="fotos_seguimiento")
    archivo = models.FileField(upload_to=ruta_foto_seguimiento)
    descripcion = models.CharField(max_length=255, blank=True)
    fecha_envio = models.DateTimeField(default=timezone.now)
    enviado_al_cliente = models.BooleanField(default=True)

    class Meta:
        ordering = ["-fecha_envio"]
        verbose_name = "Foto de seguimiento"
        verbose_name_plural = "Fotos de seguimiento"

    def __str__(self):
        return f"{self.cliente} - {self.fecha_envio:%d/%m/%Y %H:%M}"

    def clean(self):
        if self.seguimiento_id and self.cliente_id and self.seguimiento.cliente_id != self.cliente_id:
            raise ValidationError("La foto debe pertenecer al mismo cliente del seguimiento.")

    def save(self, *args, **kwargs):
        if self.seguimiento_id:
            self.cliente = self.seguimiento.cliente
        super().save(*args, **kwargs)
