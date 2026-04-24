from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import DetailView, ListView

from apps.seguimiento.models import FotoSeguimiento, SeguimientoCliente
from apps.usuarios.mixins import SoloPersonalMixin

from .forms import ClienteForm, UbicacionClienteFormSet
from .models import Cliente


class ClienteListView(LoginRequiredMixin, SoloPersonalMixin, ListView):
    model = Cliente
    template_name = "clientes/cliente_list.html"
    context_object_name = "clientes"
    paginate_by = 15

    def get_queryset(self):
        queryset = super().get_queryset().prefetch_related("ubicaciones")
        q = self.request.GET.get("q")
        if q:
            queryset = queryset.filter(
                Q(nombre_completo__icontains=q)
                | Q(identificacion__icontains=q)
                | Q(telefono__icontains=q)
                | Q(ubicacion_cliente__icontains=q)
                | Q(ubicaciones__enlace__icontains=q)
                | Q(ubicaciones__descripcion__icontains=q)
                | Q(direccion__icontains=q)
                | Q(observaciones__icontains=q)
            ).distinct()
        return queryset


class ClienteDetailView(LoginRequiredMixin, SoloPersonalMixin, DetailView):
    model = Cliente
    template_name = "clientes/cliente_detail.html"
    context_object_name = "cliente"

    def get_queryset(self):
        return super().get_queryset().prefetch_related("ubicaciones")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cliente = self.object
        context["seguimientos_pendientes"] = cliente.seguimientos.exclude(
            estado=SeguimientoCliente.Estado.COMPLETADO
        ).exclude(estado=SeguimientoCliente.Estado.CANCELADO)[:8]
        context["ultimos_seguimientos"] = cliente.seguimientos.all()[:10]
        context["ubicaciones"] = cliente.ubicaciones_lista()

        fotos = FotoSeguimiento.objects.filter(cliente=cliente).select_related("seguimiento")
        fecha = self.request.GET.get("fecha")
        if fecha:
            fotos = fotos.filter(fecha_envio__date=fecha)
        context["fotos"] = fotos[:12]
        context["filtro_fecha_foto"] = fecha or ""
        return context


class ClienteManageView(LoginRequiredMixin, SoloPersonalMixin, View):
    template_name = "clientes/cliente_form.html"
    object = None

    def get_object(self):
        return None

    def get_form(self, data=None):
        kwargs = {}
        if self.object:
            kwargs["instance"] = self.object
        if data is not None:
            kwargs["data"] = data
        return ClienteForm(**kwargs)

    def get_formset(self, data=None):
        kwargs = {"prefix": "ubicaciones"}
        if self.object:
            kwargs["instance"] = self.object
        if data is not None:
            kwargs["data"] = data
        return UbicacionClienteFormSet(**kwargs)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        formset = self.get_formset()
        return render(request, self.template_name, self.get_context_data(form, formset))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form(request.POST)
        formset = self.get_formset(request.POST)
        if form.is_valid() and formset.is_valid():
            cliente = form.save()
            formset.instance = cliente
            formset.save()
            return HttpResponseRedirect(self.get_success_url(cliente))
        return render(request, self.template_name, self.get_context_data(form, formset))

    def get_success_url(self, cliente):
        return reverse("clientes:detalle", args=[cliente.pk])

    def get_context_data(self, form, formset):
        return {
            "form": form,
            "formset": formset,
            "object": self.object,
        }


class ClienteCreateView(ClienteManageView):
    pass


class ClienteUpdateView(ClienteManageView):
    def get_object(self):
        return get_object_or_404(Cliente, pk=self.kwargs["pk"])
