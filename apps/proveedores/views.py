from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.usuarios.mixins import SoloAdministradorMixin

from .forms import ProveedorForm
from .models import Proveedor


class ProveedorListView(LoginRequiredMixin, SoloAdministradorMixin, ListView):
    model = Proveedor
    template_name = "proveedores/proveedor_list.html"
    context_object_name = "proveedores"
    paginate_by = 15

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get("q")
        if q:
            queryset = queryset.filter(Q(empresa__icontains=q) | Q(contacto__icontains=q) | Q(correo__icontains=q))
        return queryset


class ProveedorDetailView(LoginRequiredMixin, SoloAdministradorMixin, DetailView):
    model = Proveedor
    template_name = "proveedores/proveedor_detail.html"
    context_object_name = "proveedor"


class ProveedorCreateView(LoginRequiredMixin, SoloAdministradorMixin, CreateView):
    model = Proveedor
    form_class = ProveedorForm
    template_name = "proveedores/proveedor_form.html"
    success_url = reverse_lazy("proveedores:lista")


class ProveedorUpdateView(LoginRequiredMixin, SoloAdministradorMixin, UpdateView):
    model = Proveedor
    form_class = ProveedorForm
    template_name = "proveedores/proveedor_form.html"
    success_url = reverse_lazy("proveedores:lista")
