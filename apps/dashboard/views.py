from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.shortcuts import redirect
from django.views.decorators.http import require_GET
from django.views.generic import TemplateView

from apps.catalogo.models import Producto
from apps.clientes.models import Cliente
from apps.inventario.models import MovimientoStock, StockProducto
from apps.seguimiento.models import SeguimientoCliente


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/inicio.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_clientes"] = Cliente.objects.count()
        context["total_productos"] = Producto.objects.count()
        context["seguimientos_pendientes"] = SeguimientoCliente.objects.exclude(
            estado=SeguimientoCliente.Estado.COMPLETADO
        ).exclude(estado=SeguimientoCliente.Estado.CANCELADO).count()
        context["citas_agendadas"] = SeguimientoCliente.objects.filter(
            tipo_interaccion=SeguimientoCliente.TipoInteraccion.CITA,
            estado__in=[SeguimientoCliente.Estado.AGENDADO, SeguimientoCliente.Estado.EN_PROCESO],
        ).count()
        context["total_stock_casa"] = StockProducto.objects.filter(ubicacion=StockProducto.Ubicacion.CASA).aggregate(
            total=Sum("cantidad")
        ).get("total") or 0
        context["total_stock_local"] = StockProducto.objects.filter(ubicacion=StockProducto.Ubicacion.LOCAL).aggregate(
            total=Sum("cantidad")
        ).get("total") or 0
        context["seguimientos_pendientes_lista"] = (
            SeguimientoCliente.objects.exclude(estado=SeguimientoCliente.Estado.COMPLETADO)
            .exclude(estado=SeguimientoCliente.Estado.CANCELADO)
            .select_related("cliente")
            .order_by("fecha_cita", "proximo_contacto", "-fecha_interaccion")[:10]
        )
        context["movimientos_recientes"] = MovimientoStock.objects.select_related("producto")[:8]
        return context


@login_required
@require_GET
def cambiar_tema(request, tema):
    temas_validos = {"coral", "claro"}
    if tema in temas_validos:
        request.session["panel_theme"] = tema

    destino = request.GET.get("next") or request.META.get("HTTP_REFERER") or "/"
    return redirect(destino)
