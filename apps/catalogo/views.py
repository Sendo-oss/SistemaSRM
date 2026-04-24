from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.usuarios.mixins import SoloAdministradorMixin
from apps.ventas.models import DetallePedido, Pedido

from .forms import ProductoForm
from .models import CategoriaProducto, Producto


class ProductoListView(LoginRequiredMixin, SoloAdministradorMixin, ListView):
    model = Producto
    template_name = "catalogo/producto_list.html"
    context_object_name = "productos"
    paginate_by = 15

    def get_queryset(self):
        queryset = super().get_queryset().select_related("categoria")
        q = self.request.GET.get("q")
        if q:
            queryset = queryset.filter(Q(nombre__icontains=q) | Q(descripcion__icontains=q))
        return queryset


class ProductoDetailView(LoginRequiredMixin, SoloAdministradorMixin, DetailView):
    model = Producto
    template_name = "catalogo/producto_detail.html"
    context_object_name = "producto"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        producto = self.object

        ventas_qs = (
            DetallePedido.objects.filter(producto=producto)
            .exclude(pedido__estado=Pedido.Estado.CANCELADO)
            .select_related("pedido")
        )

        ventas_mensuales = list(
            ventas_qs.annotate(mes=TruncMonth("pedido__fecha_pedido"))
            .values("mes")
            .annotate(
                unidades_vendidas=Sum("cantidad"),
                ingresos=Sum("subtotal"),
                pedidos=Count("pedido", distinct=True),
            )
            .order_by("-mes")
        )

        total_unidades = ventas_qs.aggregate(total=Sum("cantidad")).get("total") or 0
        total_ingresos = ventas_qs.aggregate(total=Sum("subtotal")).get("total") or Decimal("0.00")
        ultima_venta = ventas_qs.order_by("-pedido__fecha_pedido").values_list("pedido__fecha_pedido", flat=True).first()
        mes_actual = ventas_mensuales[0] if ventas_mensuales else None
        max_unidades = max((item["unidades_vendidas"] or 0) for item in ventas_mensuales) if ventas_mensuales else 0

        for item in ventas_mensuales:
            unidades = item["unidades_vendidas"] or 0
            item["barra_porcentaje"] = round((unidades / max_unidades) * 100, 2) if max_unidades else 0

        context["ventas_mes_actual"] = mes_actual
        context["ventas_mensuales"] = ventas_mensuales[:12]
        context["ventas_totales_unidades"] = total_unidades
        context["ventas_totales_ingresos"] = total_ingresos
        context["ultima_venta"] = ultima_venta
        return context


class ProductoCreateView(LoginRequiredMixin, SoloAdministradorMixin, CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = "catalogo/producto_form.html"
    success_url = reverse_lazy("catalogo:lista")

    def form_valid(self, form):
        categoria, _ = CategoriaProducto.objects.get_or_create(
            nombre="Cremas",
            defaults={"descripcion": "Categoria creada automaticamente para cremas.", "estado": True},
        )
        form.instance.creado_por = self.request.user
        form.instance.categoria = categoria
        form.instance.tipo = Producto.Tipo.PRODUCTO
        form.instance.estado = Producto.Estado.ACTIVO
        return super().form_valid(form)


class ProductoUpdateView(LoginRequiredMixin, SoloAdministradorMixin, UpdateView):
    model = Producto
    form_class = ProductoForm
    template_name = "catalogo/producto_form.html"
    success_url = reverse_lazy("catalogo:lista")
