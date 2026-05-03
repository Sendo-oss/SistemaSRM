from django.conf import settings
from django.db import models


class Cliente(models.Model):
    class Estado(models.TextChoices):
        ACTIVO = "ACTIVO", "Activo"
        INACTIVO = "INACTIVO", "Inactivo"

    class EstadoContacto(models.TextChoices):
        NO = "NO", "No"
        LLAMA_JUAN = "LLAMA_JUAN", "Si Llama Juan"
        LLAMA_ALEX = "LLAMA_ALEX", "Si Llama Alex"
        SMS_ALEX = "SMS_ALEX", "Se envia SMS ALEX"
        SMS_JUAN = "SMS_JUAN", "Se envia SMS Juan"

    nombre_completo = models.CharField(max_length=180, blank=True)
    identificacion = models.CharField(max_length=20, unique=True, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True)
    ubicacion_cliente = models.CharField(max_length=500, blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    observaciones = models.TextField(blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ACTIVO)
    estado_contacto = models.CharField(
        max_length=30,
        choices=EstadoContacto.choices,
        default=EstadoContacto.NO,
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_registro", "-id"]
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return self.nombre_completo or self.telefono or self.identificacion or f"Cliente {self.pk}"

    @property
    def nombre_mostrado(self):
        return str(self)

    @property
    def telefono_whatsapp(self):
        digitos = "".join(caracter for caracter in self.telefono if caracter.isdigit())
        if not digitos:
            return ""
        if len(digitos) == 10 and digitos.startswith("0"):
            return f"593{digitos[1:]}"
        if len(digitos) == 9:
            return f"593{digitos}"
        return digitos

    @property
    def whatsapp_url(self):
        if not self.telefono_whatsapp:
            return ""
        return f"https://wa.me/{self.telefono_whatsapp}"

    @property
    def estado_contacto_clase(self):
        clases = {
            self.EstadoContacto.NO: "status-no",
            self.EstadoContacto.LLAMA_JUAN: "status-juan",
            self.EstadoContacto.LLAMA_ALEX: "status-alex",
            self.EstadoContacto.SMS_ALEX: "status-sms-alex",
            self.EstadoContacto.SMS_JUAN: "status-sms-juan",
        }
        return clases.get(self.estado_contacto, "status-no")

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


class ObservacionCliente(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="observaciones_historial")
    texto = models.TextField()
    fecha_registro = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="observaciones_clientes",
    )

    class Meta:
        ordering = ["-fecha_registro", "-id"]
        verbose_name = "Observacion del cliente"
        verbose_name_plural = "Observaciones del cliente"

    def __str__(self):
        return f"{self.cliente} - {self.fecha_registro:%d/%m/%Y %H:%M}"
