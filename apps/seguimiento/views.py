import calendar
from collections import defaultdict
from datetime import date

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from apps.clientes.models import Cliente
from apps.usuarios.mixins import SoloPersonalMixin

from .forms import FotoSeguimientoFormSet, SeguimientoClienteForm
from .models import FotoSeguimiento, SeguimientoCliente


class SeguimientoListView(LoginRequiredMixin, SoloPersonalMixin, ListView):
    model = SeguimientoCliente
    template_name = "seguimiento/seguimiento_list.html"
    context_object_name = "seguimientos"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related("cliente", "usuario")
        q = self.request.GET.get("q")
        estado = self.request.GET.get("estado")
        tipo = self.request.GET.get("tipo")

        if q:
            queryset = queryset.filter(
                Q(cliente__nombre_completo__icontains=q)
                | Q(cliente__telefono__icontains=q)
                | Q(cliente__ubicacion_cliente__icontains=q)
                | Q(cliente__direccion__icontains=q)
                | Q(observacion__icontains=q)
                | Q(asunto__icontains=q)
            )

        if estado:
            queryset = queryset.filter(estado=estado)
        if tipo:
            queryset = queryset.filter(tipo_interaccion=tipo)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["estados"] = SeguimientoCliente.Estado.choices
        context["tipos"] = SeguimientoCliente.TipoInteraccion.choices
        return context


class SeguimientoDetailView(LoginRequiredMixin, SoloPersonalMixin, DetailView):
    model = SeguimientoCliente
    template_name = "seguimiento/seguimiento_detail.html"
    context_object_name = "seguimiento"


class SeguimientoManageView(LoginRequiredMixin, SoloPersonalMixin, View):
    template_name = "seguimiento/seguimiento_form.html"
    object = None

    def get_object(self):
        return None

    def get_initial(self):
        initial = {}
        cliente_id = self.request.GET.get("cliente")
        tipo = self.request.GET.get("tipo")
        if cliente_id:
            initial["cliente"] = cliente_id
        if tipo:
            initial["tipo_interaccion"] = tipo
        return initial

    def get_form(self, data=None, files=None):
        kwargs = {"initial": self.get_initial()}
        if self.object:
            kwargs["instance"] = self.object
        if data is not None:
            kwargs["data"] = data
        if files is not None:
            kwargs["files"] = files
        return SeguimientoClienteForm(**kwargs)

    def get_formset(self, data=None, files=None):
        kwargs = {"prefix": "fotos"}
        if self.object:
            kwargs["instance"] = self.object
        if data is not None:
            kwargs["data"] = data
        if files is not None:
            kwargs["files"] = files
        return FotoSeguimientoFormSet(**kwargs)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        formset = self.get_formset()
        return render(request, self.template_name, self.get_context_data(form, formset))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form(request.POST, request.FILES)
        formset = self.get_formset(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            seguimiento = form.save(commit=False)
            if not seguimiento.pk:
                seguimiento.usuario = request.user
            seguimiento.save()
            formset.instance = seguimiento
            formset.save()
            return HttpResponseRedirect(self.get_success_url(seguimiento))
        return render(request, self.template_name, self.get_context_data(form, formset))

    def get_success_url(self, seguimiento):
        if seguimiento.tipo_interaccion == SeguimientoCliente.TipoInteraccion.CITA:
            return reverse("seguimiento:agenda")
        return reverse("seguimiento:detalle", args=[seguimiento.pk])

    def get_context_data(self, form, formset):
        cliente_id = self.request.GET.get("cliente")
        cliente = None
        if self.object:
            cliente = self.object.cliente
        elif cliente_id:
            cliente = get_object_or_404(Cliente, pk=cliente_id)
        return {
            "form": form,
            "formset": formset,
            "object": self.object,
            "cliente_preseleccionado": cliente,
        }


class SeguimientoCreateView(SeguimientoManageView):
    pass


class SeguimientoUpdateView(SeguimientoManageView):
    def get_object(self):
        return get_object_or_404(SeguimientoCliente, pk=self.kwargs["pk"])


class AgendaCitasView(LoginRequiredMixin, SoloPersonalMixin, TemplateView):
    template_name = "seguimiento/agenda.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoy = date.today()
        year = int(self.request.GET.get("year", hoy.year))
        month = int(self.request.GET.get("month", hoy.month))

        calendario = calendar.Calendar(firstweekday=0)
        citas = (
            SeguimientoCliente.objects.filter(
                tipo_interaccion=SeguimientoCliente.TipoInteraccion.CITA,
                fecha_cita__year=year,
                fecha_cita__month=month,
            )
            .select_related("cliente")
            .order_by("fecha_cita")
        )

        citas_por_dia = defaultdict(list)
        for cita in citas:
            citas_por_dia[cita.fecha_cita.date()].append(cita)

        semanas = []
        for semana in calendario.monthdatescalendar(year, month):
            dias = []
            for dia in semana:
                dias.append(
                    {
                        "fecha": dia,
                        "en_mes": dia.month == month,
                        "citas": citas_por_dia.get(dia, []),
                    }
                )
            semanas.append(dias)

        mes_anterior = date(year - 1, 12, 1) if month == 1 else date(year, month - 1, 1)
        mes_siguiente = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)

        context.update(
            {
                "semanas": semanas,
                "mes_actual": date(year, month, 1),
                "mes_anterior": mes_anterior,
                "mes_siguiente": mes_siguiente,
                "citas_proximas": SeguimientoCliente.objects.filter(
                    tipo_interaccion=SeguimientoCliente.TipoInteraccion.CITA,
                    fecha_cita__gte=timezone.now(),
                )
                .select_related("cliente")
                .order_by("fecha_cita")[:10],
            }
        )
        return context


class FotoSeguimientoListView(LoginRequiredMixin, SoloPersonalMixin, ListView):
    model = FotoSeguimiento
    template_name = "seguimiento/foto_list.html"
    context_object_name = "fotos"
    paginate_by = 24

    def get_queryset(self):
        queryset = super().get_queryset().select_related("cliente", "seguimiento")
        q = self.request.GET.get("q")
        cliente_id = self.request.GET.get("cliente")
        fecha = self.request.GET.get("fecha")

        if q:
            queryset = queryset.filter(
                Q(cliente__nombre_completo__icontains=q)
                | Q(cliente__telefono__icontains=q)
                | Q(descripcion__icontains=q)
                | Q(seguimiento__asunto__icontains=q)
            )
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        if fecha:
            queryset = queryset.filter(fecha_envio__date=fecha)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["clientes"] = Cliente.objects.order_by("nombre_completo", "telefono")
        return context
