from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.usuarios.mixins import SoloAdministradorMixin

from .forms import PromocionForm
from .models import Promocion


class PromocionListView(LoginRequiredMixin, SoloAdministradorMixin, ListView):
    model = Promocion
    template_name = "promociones/promocion_list.html"
    context_object_name = "promociones"
    paginate_by = 15

    def get_queryset(self):
        queryset = super().get_queryset().select_related("producto")
        q = self.request.GET.get("q")
        if q:
            queryset = queryset.filter(
                Q(nombre__icontains=q)
                | Q(descripcion__icontains=q)
                | Q(producto__nombre__icontains=q)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        promociones = context["promociones"]
        context["descuentos_rentables"] = sum(1 for item in promociones if item.es_rentable is True)
        context["descuentos_no_rentables"] = sum(1 for item in promociones if item.es_rentable is False)
        return context


class PromocionDetailView(LoginRequiredMixin, SoloAdministradorMixin, DetailView):
    model = Promocion
    template_name = "promociones/promocion_detail.html"
    context_object_name = "promocion"


class PromocionCreateView(LoginRequiredMixin, SoloAdministradorMixin, CreateView):
    model = Promocion
    form_class = PromocionForm
    template_name = "promociones/promocion_form.html"
    success_url = reverse_lazy("promociones:lista")


class PromocionUpdateView(LoginRequiredMixin, SoloAdministradorMixin, UpdateView):
    model = Promocion
    form_class = PromocionForm
    template_name = "promociones/promocion_form.html"
    success_url = reverse_lazy("promociones:lista")
