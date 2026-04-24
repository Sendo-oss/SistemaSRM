from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.usuarios.mixins import SoloAdministradorMixin
from apps.catalogo.models import Producto
from apps.promociones.models import Promocion

from .forms import DetallePedidoFormSet, PedidoForm
from .models import Pedido


class PedidoListView(LoginRequiredMixin, SoloAdministradorMixin, ListView):
    model = Pedido
    template_name = "ventas/pedido_list.html"
    context_object_name = "pedidos"
    paginate_by = 15

    def get_queryset(self):
        queryset = super().get_queryset().select_related("cliente", "promocion")
        q = self.request.GET.get("q")
        if q:
            queryset = queryset.filter(
                Q(cliente__nombre_completo__icontains=q)
                | Q(cliente__identificacion__icontains=q)
            )
        return queryset


class PedidoDetailView(LoginRequiredMixin, SoloAdministradorMixin, DetailView):
    model = Pedido
    template_name = "ventas/pedido_detail.html"
    context_object_name = "pedido"

    def get_queryset(self):
        return super().get_queryset().select_related("cliente", "promocion", "usuario").prefetch_related("detalles__producto")

class PedidoCreateView(LoginRequiredMixin, SoloAdministradorMixin, CreateView):
    http_method_names = ["get", "post"]

    def build_context(self, form, formset, object=None):
        return {
            "form": form,
            "formset": formset,
            "object": object,
            "productos_json": list(
                Producto.objects.filter(estado=Producto.Estado.ACTIVO).values("id", "nombre", "precio")
            ),
            "promociones_json": list(
                Promocion.objects.filter(activa=True).values("id", "nombre", "porcentaje_descuento", "monto_descuento")
            ),
        }

    def build_detail_maps(self, formset):
        desired = {}
        for form in formset.forms:
            if not hasattr(form, "cleaned_data") or not form.cleaned_data:
                continue
            if form.cleaned_data.get("DELETE"):
                continue
            producto = form.cleaned_data.get("producto")
            cantidad = form.cleaned_data.get("cantidad")
            if producto and cantidad:
                desired[producto.pk] = desired.get(producto.pk, 0) + int(cantidad)
        return desired

    def get_existing_detail_map(self, pedido):
        existing = {}
        for detalle in pedido.detalles.all():
            existing[detalle.producto_id] = existing.get(detalle.producto_id, 0) + int(detalle.cantidad)
        return existing

    def validate_stock(self, previous_details, desired_details, target_state):
        if target_state == Pedido.Estado.CANCELADO:
            return None
        errores = []
        productos = Producto.objects.in_bulk(set(previous_details.keys()) | set(desired_details.keys()))
        for producto_id, producto in productos.items():
            previo = previous_details.get(producto_id, 0)
            nuevo = desired_details.get(producto_id, 0)
            disponible = producto.stock_disponible + previo
            if nuevo > disponible:
                errores.append(
                    f"Stock insuficiente para {producto.nombre}. Disponible: {disponible}, solicitado: {nuevo}."
                )
        return errores

    def apply_stock_changes(self, previous_details, desired_details, previous_state, target_state):
        productos = Producto.objects.select_for_update().in_bulk(set(previous_details.keys()) | set(desired_details.keys()))
        for producto_id, producto in productos.items():
            previo = previous_details.get(producto_id, 0) if previous_state != Pedido.Estado.CANCELADO else 0
            nuevo = desired_details.get(producto_id, 0) if target_state != Pedido.Estado.CANCELADO else 0
            delta = previo - nuevo
            producto.stock_disponible = producto.stock_disponible + delta
            producto.save(update_fields=["stock_disponible"])

    def get(self, request, *args, **kwargs):
        form = PedidoForm()
        formset = DetallePedidoFormSet(prefix="detalles")
        return render(request, "ventas/pedido_form.html", self.build_context(form, formset))

    def post(self, request, *args, **kwargs):
        form = PedidoForm(request.POST)
        formset = DetallePedidoFormSet(request.POST, prefix="detalles")
        if form.is_valid() and formset.is_valid():
            desired_details = self.build_detail_maps(formset)
            errores_stock = self.validate_stock({}, desired_details, form.cleaned_data["estado"])
            if errores_stock:
                for error in errores_stock:
                    messages.error(request, error)
                return render(request, "ventas/pedido_form.html", self.build_context(form, formset))

            with transaction.atomic():
                pedido = form.save(commit=False)
                pedido.usuario = request.user
                pedido.subtotal = 0
                pedido.descuento = 0
                pedido.total = 0
                pedido.save()
                formset.instance = pedido
                detalles = formset.save(commit=False)
                for detalle in detalles:
                    detalle.save()
                for obj in formset.deleted_objects:
                    obj.delete()
                pedido.recalcular_totales()
                self.apply_stock_changes({}, desired_details, None, pedido.estado)
                pedido.actualizar_estado_por_pagos()
                messages.success(request, "Pedido creado correctamente.")
                return redirect("ventas:detalle", pk=pedido.pk)
        return render(request, "ventas/pedido_form.html", self.build_context(form, formset))


class PedidoUpdateView(LoginRequiredMixin, SoloAdministradorMixin, UpdateView):
    http_method_names = ["get", "post"]

    def get_object(self, queryset=None):
        return Pedido.objects.get(pk=self.kwargs["pk"])

    def get(self, request, *args, **kwargs):
        pedido = self.get_object()
        form = PedidoForm(instance=pedido)
        formset = DetallePedidoFormSet(instance=pedido, prefix="detalles")
        return render(request, "ventas/pedido_form.html", PedidoCreateView().build_context(form, formset, pedido))

    def post(self, request, *args, **kwargs):
        pedido = self.get_object()
        form = PedidoForm(request.POST, instance=pedido)
        formset = DetallePedidoFormSet(request.POST, instance=pedido, prefix="detalles")
        if form.is_valid() and formset.is_valid():
            previous_state = pedido.estado
            previous_details = self.get_existing_detail_map(pedido)
            desired_details = self.build_detail_maps(formset)
            errores_stock = self.validate_stock(previous_details, desired_details, form.cleaned_data["estado"])
            if errores_stock:
                for error in errores_stock:
                    messages.error(request, error)
                return render(request, "ventas/pedido_form.html", PedidoCreateView().build_context(form, formset, pedido))

            with transaction.atomic():
                pedido = form.save()
                detalles = formset.save(commit=False)
                for detalle in detalles:
                    detalle.save()
                for obj in formset.deleted_objects:
                    obj.delete()
                pedido.recalcular_totales()
                self.apply_stock_changes(previous_details, desired_details, previous_state, pedido.estado)
                pedido.actualizar_estado_por_pagos()
                messages.success(request, "Pedido actualizado correctamente.")
                return redirect("ventas:detalle", pk=pedido.pk)
        return render(request, "ventas/pedido_form.html", PedidoCreateView().build_context(form, formset, pedido))
