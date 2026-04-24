from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.usuarios.mixins import SoloAdministradorMixin

from .forms import PagoForm
from .models import Pago


class PagoListView(LoginRequiredMixin, SoloAdministradorMixin, ListView):
    model = Pago
    template_name = "pagos/pago_list.html"
    context_object_name = "pagos"
    paginate_by = 15

    def get_queryset(self):
        queryset = super().get_queryset().select_related("pedido", "pedido__cliente")
        q = self.request.GET.get("q")
        if q:
            queryset = queryset.filter(
                Q(referencia__icontains=q)
                | Q(pedido__cliente__nombre_completo__icontains=q)
            )
        return queryset


class PagoDetailView(LoginRequiredMixin, SoloAdministradorMixin, DetailView):
    model = Pago
    template_name = "pagos/pago_detail.html"
    context_object_name = "pago"


class PagoCreateView(LoginRequiredMixin, SoloAdministradorMixin, CreateView):
    model = Pago
    form_class = PagoForm
    template_name = "pagos/pago_form.html"
    success_url = reverse_lazy("pagos:lista")

    def get_initial(self):
        initial = super().get_initial()
        pedido = self.request.GET.get("pedido")
        if pedido:
            initial["pedido"] = pedido
        return initial

    def form_valid(self, form):
        messages.success(self.request, "Pago registrado correctamente.")
        return super().form_valid(form)


class PagoUpdateView(LoginRequiredMixin, SoloAdministradorMixin, UpdateView):
    model = Pago
    form_class = PagoForm
    template_name = "pagos/pago_form.html"
    success_url = reverse_lazy("pagos:lista")

    def form_valid(self, form):
        messages.success(self.request, "Pago actualizado correctamente.")
        return super().form_valid(form)
