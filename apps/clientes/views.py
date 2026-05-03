from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q, Sum
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

from apps.seguimiento.forms import FotoSeguimientoFormSet
from apps.seguimiento.models import FotoSeguimiento, SeguimientoCliente
from apps.usuarios.mixins import SoloPersonalMixin
from apps.ventas.models import DetallePedido, Pedido

from .forms import ClienteForm, CompraClienteRapidaFormSet, GestionInicialForm, ObservacionClienteForm
from .models import Cliente, ObservacionCliente


class ClienteListView(LoginRequiredMixin, SoloPersonalMixin, ListView):
    model = Cliente
    template_name = "clientes/cliente_list.html"
    context_object_name = "clientes"
    paginate_by = 15

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get("q")
        estado = self.request.GET.get("estado")
        estado_contacto = self.request.GET.get("estado_contacto")
        fecha_desde = self.request.GET.get("fecha_desde")
        fecha_hasta = self.request.GET.get("fecha_hasta")
        tratamiento = self.request.GET.get("tratamiento")
        fotos = self.request.GET.get("fotos")

        if q:
            queryset = queryset.filter(
                Q(nombre_completo__icontains=q)
                | Q(telefono__icontains=q)
                | Q(direccion__icontains=q)
                | Q(observaciones__icontains=q)
                | Q(observaciones_historial__texto__icontains=q)
            ).distinct()
        if estado:
            queryset = queryset.filter(estado=estado)
        if estado_contacto:
            queryset = queryset.filter(estado_contacto=estado_contacto)
        if fecha_desde:
            queryset = queryset.filter(fecha_registro__date__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_registro__date__lte=fecha_hasta)
        if tratamiento == "si":
            queryset = queryset.filter(seguimientos__tratamiento_aceptado=True).distinct()
        elif tratamiento == "no":
            queryset = queryset.exclude(seguimientos__tratamiento_aceptado=True)
        if fotos == "pendientes":
            queryset = queryset.filter(
                seguimientos__tipo_interaccion=SeguimientoCliente.TipoInteraccion.FOTOS_PENDIENTES,
                seguimientos__estado__in=[
                    SeguimientoCliente.Estado.PENDIENTE,
                    SeguimientoCliente.Estado.AGENDADO,
                    SeguimientoCliente.Estado.EN_PROCESO,
                ],
            ).distinct()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["estados_cliente"] = Cliente.Estado.choices
        context["estados_contacto"] = Cliente.EstadoContacto.choices
        return context


class ClienteEstadoContactoUpdateView(LoginRequiredMixin, SoloPersonalMixin, View):
    def post(self, request, pk):
        cliente = get_object_or_404(Cliente, pk=pk)
        estado_contacto = request.POST.get("estado_contacto")
        estados_validos = {value for value, _label in Cliente.EstadoContacto.choices}
        if estado_contacto in estados_validos:
            cliente.estado_contacto = estado_contacto
            cliente.save(update_fields=["estado_contacto"])

        return HttpResponseRedirect(request.POST.get("next") or reverse("clientes:lista"))


class ClienteQuickCreateView(LoginRequiredMixin, SoloPersonalMixin, View):
    def post(self, request):
        nombre = (request.POST.get("nombre_completo") or "").strip()
        telefono = (request.POST.get("telefono") or "").strip()
        direccion = (request.POST.get("direccion") or "").strip()
        observacion = (request.POST.get("observacion") or "").strip()
        estado_contacto = request.POST.get("estado_contacto") or Cliente.EstadoContacto.NO
        next_url = request.POST.get("next") or reverse("clientes:lista")
        is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

        if not nombre and not telefono:
            if is_ajax:
                return JsonResponse(
                    {"ok": False, "error": "Ingresa al menos nombre o telefono."},
                    status=400,
                )
            messages.error(request, "Ingresa al menos nombre o telefono para crear el cliente rapido.")
            return HttpResponseRedirect(next_url)

        estados_validos = {value for value, _label in Cliente.EstadoContacto.choices}
        if estado_contacto not in estados_validos:
            estado_contacto = Cliente.EstadoContacto.NO

        cliente = Cliente.objects.create(
            nombre_completo=nombre,
            telefono=telefono,
            direccion=direccion,
            estado_contacto=estado_contacto,
        )
        if observacion:
            ObservacionCliente.objects.create(cliente=cliente, texto=observacion, usuario=request.user)

        if is_ajax:
            return JsonResponse(
                {
                    "ok": True,
                    "cliente_id": cliente.pk,
                    "edit_url": reverse("clientes:editar", args=[cliente.pk]),
                    "detail_url": reverse("clientes:detalle", args=[cliente.pk]),
                }
            )

        messages.success(request, "Cliente rapido guardado.")

        if request.POST.get("quick_action") == "complete":
            return HttpResponseRedirect(reverse("clientes:editar", args=[cliente.pk]))
        return HttpResponseRedirect(next_url)


class ClienteObservacionCreateView(LoginRequiredMixin, SoloPersonalMixin, View):
    def post(self, request, pk):
        cliente = get_object_or_404(Cliente, pk=pk)
        form = ObservacionClienteForm(request.POST)
        next_url = request.POST.get("next") or reverse("clientes:detalle", args=[cliente.pk])
        if form.is_valid():
            observacion = form.save(commit=False)
            observacion.cliente = cliente
            observacion.usuario = request.user
            observacion.save()
            messages.success(request, "Observacion agregada.")
        return HttpResponseRedirect(next_url)


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

    def get_gestion_form(self, data=None):
        initial = {}
        tipo = self.request.GET.get("tipo")
        tipos_validos = {value for value, _label in SeguimientoCliente.TipoInteraccion.choices}
        if tipo in tipos_validos:
            initial["tipo_interaccion"] = tipo
        if tipo == SeguimientoCliente.TipoInteraccion.FOTOS_PENDIENTES:
            initial["fotos_pendientes"] = True
            initial["asunto"] = "Fotos pendientes"

        kwargs = {"prefix": "gestion", "initial": initial}
        if data is not None:
            kwargs["data"] = data
        return GestionInicialForm(**kwargs)

    def get_foto_formset(self, prefix, data=None, files=None):
        kwargs = {"prefix": prefix}
        if data is not None:
            kwargs["data"] = data
        if files is not None:
            kwargs["files"] = files
        return FotoSeguimientoFormSet(**kwargs)

    def get_compra_formset(self, data=None):
        kwargs = {"prefix": "compras"}
        if data is not None:
            kwargs["data"] = data
        return CompraClienteRapidaFormSet(**kwargs)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        gestion_form = self.get_gestion_form()
        fotos_recibidas_formset = self.get_foto_formset("fotos_recibidas")
        fotos_enviadas_formset = self.get_foto_formset("fotos_enviadas")
        compras_formset = self.get_compra_formset()
        return render(
            request,
            self.template_name,
            self.get_context_data(form, gestion_form, fotos_recibidas_formset, fotos_enviadas_formset, compras_formset),
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form(request.POST)
        gestion_form = self.get_gestion_form(request.POST)
        fotos_recibidas_formset = self.get_foto_formset("fotos_recibidas", request.POST, request.FILES)
        fotos_enviadas_formset = self.get_foto_formset("fotos_enviadas", request.POST, request.FILES)
        compras_formset = self.get_compra_formset(request.POST)

        if (
            form.is_valid()
            and gestion_form.is_valid()
            and fotos_recibidas_formset.is_valid()
            and fotos_enviadas_formset.is_valid()
            and compras_formset.is_valid()
        ):
            has_fotos_recibidas = self.formset_tiene_datos(fotos_recibidas_formset)
            has_fotos_enviadas = self.formset_tiene_datos(fotos_enviadas_formset)
            has_files = has_fotos_recibidas or has_fotos_enviadas
            gestion_se_guarda = gestion_form.should_save(has_files=has_files)
            tiene_observacion = bool((request.POST.get("nueva_observacion") or "").strip())
            compras_a_guardar = sum(
                1
                for compra_form in compras_formset.forms
                if getattr(compra_form, "cleaned_data", None)
                and compra_form.cleaned_data.get("guardar_compra")
                and not compra_form.cleaned_data.get("DELETE")
            )
            fotos_a_eliminar = len(request.POST.getlist("eliminar_fotos"))
            compras_a_eliminar = len(request.POST.getlist("eliminar_pedidos"))
            try:
                with transaction.atomic():
                    cliente = form.save()
                    self.guardar_observacion(request.POST.get("nueva_observacion"), cliente, request.user)
                    if gestion_se_guarda:
                        seguimiento = self.crear_gestion_inicial(
                            cliente,
                            gestion_form,
                            request.user,
                            has_files,
                            has_fotos_recibidas=has_fotos_recibidas,
                            has_fotos_enviadas=has_fotos_enviadas,
                        )
                        self.guardar_fotos(fotos_recibidas_formset, seguimiento, enviado_al_cliente=False)
                        self.guardar_fotos(fotos_enviadas_formset, seguimiento, enviado_al_cliente=True)
                    self.eliminar_fotos(request.POST.getlist("eliminar_fotos"), cliente)
                    self.eliminar_compras(request.POST.getlist("eliminar_pedidos"), cliente)
                    self.guardar_compras(compras_formset, cliente, request.user)
            except ValueError:
                return render(
                    request,
                    self.template_name,
                    self.get_context_data(form, gestion_form, fotos_recibidas_formset, fotos_enviadas_formset, compras_formset),
                )

            acciones = []
            if tiene_observacion:
                acciones.append("observacion agregada")
            if gestion_se_guarda:
                acciones.append("seguimiento creado")
            if has_files:
                acciones.append("fotos guardadas")
            if compras_a_guardar:
                acciones.append("compra registrada" if compras_a_guardar == 1 else f"{compras_a_guardar} compras registradas")
            if fotos_a_eliminar:
                acciones.append("fotos eliminadas")
            if compras_a_eliminar:
                acciones.append("compras eliminadas")
            detalle = f": {', '.join(acciones)}" if acciones else ""
            messages.success(request, f"Ficha del cliente guardada{detalle}.")
            return HttpResponseRedirect(self.get_success_url(cliente))
        return render(
            request,
            self.template_name,
            self.get_context_data(form, gestion_form, fotos_recibidas_formset, fotos_enviadas_formset, compras_formset),
        )

    def get_success_url(self, cliente):
        if self.request.POST.get("guardar_y_volver"):
            return reverse("clientes:lista")
        return reverse("clientes:editar", args=[cliente.pk])

    def get_observacion_form(self):
        return ObservacionClienteForm()

    def crear_gestion_inicial(
        self,
        cliente,
        gestion_form,
        usuario,
        has_files=False,
        has_fotos_recibidas=False,
        has_fotos_enviadas=False,
    ):
        data = gestion_form.cleaned_data
        tipo = data.get("tipo_interaccion")
        if not tipo:
            if data.get("fotos_pendientes"):
                tipo = SeguimientoCliente.TipoInteraccion.FOTOS_PENDIENTES
            elif has_files:
                tipo = SeguimientoCliente.TipoInteraccion.ENVIO_FOTOS
            else:
                tipo = SeguimientoCliente.TipoInteraccion.SEGUIMIENTO
        fecha_cita = data.get("fecha_cita")
        proximo_contacto = data.get("proximo_contacto")
        asunto = data.get("asunto")

        if data.get("fotos_pendientes") and not asunto:
            asunto = "Fotos pendientes"
        elif has_fotos_recibidas and has_fotos_enviadas and not asunto:
            asunto = "Fotos recibidas y enviadas"
        elif has_fotos_recibidas and not asunto:
            asunto = "Fotos recibidas del cliente"
        elif has_fotos_enviadas and not asunto:
            asunto = "Fotos enviadas al cliente"
        if tipo == SeguimientoCliente.TipoInteraccion.CITA and fecha_cita and not proximo_contacto:
            proximo_contacto = fecha_cita

        seguimiento = SeguimientoCliente(
            cliente=cliente,
            tipo_interaccion=tipo,
            asunto=asunto or "",
            estado=data.get("estado") or SeguimientoCliente.Estado.PENDIENTE,
            observacion=data.get("observacion") or "",
            fecha_interaccion=fecha_cita or timezone.now(),
            fecha_cita=fecha_cita,
            proximo_contacto=proximo_contacto,
            tratamiento_aceptado=data.get("tratamiento_aceptado") or False,
            usuario=usuario,
        )
        seguimiento.full_clean()
        seguimiento.save()
        return seguimiento

    def formset_tiene_datos(self, formset):
        return any(form.has_changed() and not form.cleaned_data.get("DELETE", False) for form in formset.forms)

    def guardar_fotos(self, formset, seguimiento, enviado_al_cliente):
        formset.instance = seguimiento
        fotos = formset.save(commit=False)
        for foto in fotos:
            foto.seguimiento = seguimiento
            foto.cliente = seguimiento.cliente
            foto.enviado_al_cliente = enviado_al_cliente
            foto.save()
        for foto in formset.deleted_objects:
            foto.delete()

    def guardar_compras(self, formset, cliente, usuario):
        for compra_form in formset.forms:
            if not hasattr(compra_form, "cleaned_data") or not compra_form.cleaned_data:
                continue
            if compra_form.cleaned_data.get("DELETE") or not compra_form.cleaned_data.get("guardar_compra"):
                continue

            producto = compra_form.cleaned_data["producto"]
            cantidad = compra_form.cleaned_data["cantidad"]
            estado = compra_form.cleaned_data["estado"] or Pedido.Estado.PAGADO

            producto = producto.__class__.objects.select_for_update().get(pk=producto.pk)

            pedido = Pedido.objects.create(
                cliente=cliente,
                usuario=usuario,
                estado=estado,
                observaciones="",
                subtotal=0,
                descuento=0,
                total=0,
            )
            DetallePedido.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=producto.precio,
                subtotal=0,
            )
            pedido.recalcular_totales()
            if estado != Pedido.Estado.CANCELADO and producto.stock_disponible > 0:
                producto.stock_disponible = max(producto.stock_disponible - Decimal(cantidad), Decimal("0.00"))
                producto.save(update_fields=["stock_disponible"])

    def eliminar_compras(self, pedido_ids, cliente):
        if not pedido_ids:
            return

        pedidos = Pedido.objects.filter(pk__in=pedido_ids, cliente=cliente).prefetch_related("detalles__producto")
        for pedido in pedidos:
            if pedido.estado != Pedido.Estado.CANCELADO:
                for detalle in pedido.detalles.select_related("producto"):
                    producto = detalle.producto.__class__.objects.select_for_update().get(pk=detalle.producto_id)
                    producto.stock_disponible = producto.stock_disponible + detalle.cantidad
                    producto.save(update_fields=["stock_disponible"])
            pedido.delete()

    def eliminar_fotos(self, foto_ids, cliente):
        if not foto_ids:
            return

        for foto in FotoSeguimiento.objects.filter(pk__in=foto_ids, cliente=cliente):
            foto.archivo.delete(save=False)
            foto.delete()

    def guardar_observacion(self, texto, cliente, usuario):
        texto = (texto or "").strip()
        if texto:
            ObservacionCliente.objects.create(cliente=cliente, texto=texto, usuario=usuario)

    def get_context_data(self, form, gestion_form, fotos_recibidas_formset, fotos_enviadas_formset, compras_formset):
        pedidos_tratamiento = []
        if self.object:
            pedidos_tratamiento = (
                self.object.pedidos.prefetch_related("detalles__producto")
                .select_related("promocion", "usuario")
                .order_by("-fecha_pedido")[:10]
            )
        return {
            "form": form,
            "gestion_form": gestion_form,
            "fotos_recibidas_formset": fotos_recibidas_formset,
            "fotos_enviadas_formset": fotos_enviadas_formset,
            "compras_formset": compras_formset,
            "pedidos_tratamiento": pedidos_tratamiento,
            "productos_json": list(
                compras_formset.forms[0].fields["producto"].queryset.values("id", "nombre", "precio", "stock_disponible")
            ),
            "observacion_form": self.get_observacion_form(),
            "observaciones_historial": self.object.observaciones_historial.all()[:20] if self.object else [],
            "ultima_observacion": self.object.observaciones_historial.first() if self.object else None,
            "total_comprado": self.object.pedidos.aggregate(total=Sum("total")).get("total") or Decimal("0.00") if self.object else Decimal("0.00"),
            "object": self.object,
        }


class ClienteCreateView(ClienteManageView):
    pass


class ClienteUpdateView(ClienteManageView):
    def get_object(self):
        return get_object_or_404(Cliente, pk=self.kwargs["pk"])


class ClienteDetailView(ClienteUpdateView):
    template_name = "clientes/cliente_detail.html"

    def get_success_url(self, cliente):
        if self.request.POST.get("guardar_y_volver"):
            return reverse("clientes:lista")
        return reverse("clientes:detalle", args=[cliente.pk])

    def get_context_data(self, form, gestion_form, fotos_recibidas_formset, fotos_enviadas_formset, compras_formset):
        context = super().get_context_data(
            form,
            gestion_form,
            fotos_recibidas_formset,
            fotos_enviadas_formset,
            compras_formset,
        )
        cliente = self.object
        context["cliente"] = cliente
        context["seguimientos_pendientes"] = cliente.seguimientos.exclude(
            estado=SeguimientoCliente.Estado.COMPLETADO
        ).exclude(estado=SeguimientoCliente.Estado.CANCELADO)[:8]
        context["fotos_pendientes"] = cliente.seguimientos.filter(
            tipo_interaccion=SeguimientoCliente.TipoInteraccion.FOTOS_PENDIENTES
        ).exclude(estado=SeguimientoCliente.Estado.COMPLETADO).exclude(
            estado=SeguimientoCliente.Estado.CANCELADO
        )[:8]
        context["ultimos_seguimientos"] = cliente.seguimientos.all()[:10]
        fotos = FotoSeguimiento.objects.filter(cliente=cliente).select_related("seguimiento")
        fecha = self.request.GET.get("fecha")
        if fecha:
            fotos = fotos.filter(fecha_envio__date=fecha)
        context["fotos"] = fotos[:12]
        context["filtro_fecha_foto"] = fecha or ""
        return context
