from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView

from apps.catalogo.models import Producto
from apps.usuarios.mixins import SoloAdministradorMixin

from .forms import MovimientoStockForm
from .models import MovimientoStock, StockProducto


class InventarioListView(LoginRequiredMixin, SoloAdministradorMixin, ListView):
    model = Producto
    template_name = "inventario/inventario_list.html"
    context_object_name = "productos"
    paginate_by = 15

    def get_queryset(self):
        queryset = super().get_queryset().select_related("categoria").prefetch_related("stocks_ubicacion")
        q = self.request.GET.get("q")
        if q:
            queryset = queryset.filter(
                Q(nombre__icontains=q) | Q(descripcion__icontains=q) | Q(categoria__nombre__icontains=q)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for producto in context["productos"]:
            cantidades = {stock.ubicacion: stock.cantidad for stock in producto.stocks_ubicacion.all()}
            producto.stock_casa = cantidades.get(StockProducto.Ubicacion.CASA, 0)
            producto.stock_local = cantidades.get(StockProducto.Ubicacion.LOCAL, 0)
        context["movimientos_recientes"] = MovimientoStock.objects.select_related("producto", "usuario")[:12]
        return context


class MovimientoStockCreateView(LoginRequiredMixin, SoloAdministradorMixin, CreateView):
    model = MovimientoStock
    form_class = MovimientoStockForm
    template_name = "inventario/movimiento_form.html"
    success_url = reverse_lazy("inventario:lista")

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        return super().form_valid(form)


class MovimientoStockListView(LoginRequiredMixin, SoloAdministradorMixin, ListView):
    model = MovimientoStock
    template_name = "inventario/movimiento_list.html"
    context_object_name = "movimientos"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related("producto", "usuario")
        q = self.request.GET.get("q")
        if q:
            queryset = queryset.filter(Q(producto__nombre__icontains=q) | Q(observacion__icontains=q))
        return queryset
