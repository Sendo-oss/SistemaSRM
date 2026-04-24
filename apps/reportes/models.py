from django.db import models


class ReporteExportado(models.Model):
    nombre = models.CharField(max_length=150)
    modulo = models.CharField(max_length=50)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Reporte exportado"
        verbose_name_plural = "Reportes exportados"
