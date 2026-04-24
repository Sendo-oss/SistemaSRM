from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from .forms import UsuarioForm, UsuarioUpdateForm
from .mixins import SoloAdministradorMixin
from .models import Usuario


def cerrar_sesion(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        logout(request)
    return redirect("login")


class UsuarioListView(LoginRequiredMixin, SoloAdministradorMixin, ListView):
    model = Usuario
    template_name = "usuarios/usuario_list.html"
    context_object_name = "usuarios"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().exclude(rol=Usuario.Rol.CLIENTE)
        q = self.request.GET.get("q")
        if q:
            queryset = queryset.filter(
                Q(username__icontains=q)
                | Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(telefono__icontains=q)
            )
        return queryset.order_by("rol", "first_name", "last_name", "username")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuarios_internos = Usuario.objects.exclude(rol=Usuario.Rol.CLIENTE)
        context["total_administradores"] = usuarios_internos.filter(rol=Usuario.Rol.ADMINISTRADOR).count()
        context["total_trabajadores"] = usuarios_internos.filter(rol=Usuario.Rol.EMPLEADO).count()
        return context


class UsuarioCreateView(LoginRequiredMixin, SoloAdministradorMixin, CreateView):
    model = Usuario
    form_class = UsuarioForm
    template_name = "usuarios/usuario_form.html"
    success_url = reverse_lazy("usuarios:lista")

    def form_valid(self, form):
        messages.success(self.request, "Usuario creado correctamente.")
        return super().form_valid(form)


class UsuarioUpdateView(LoginRequiredMixin, SoloAdministradorMixin, UpdateView):
    model = Usuario
    form_class = UsuarioUpdateForm
    template_name = "usuarios/usuario_form.html"
    success_url = reverse_lazy("usuarios:lista")

    def get_queryset(self):
        return super().get_queryset().exclude(rol=Usuario.Rol.CLIENTE)

    def form_valid(self, form):
        messages.success(self.request, "Usuario actualizado correctamente.")
        return super().form_valid(form)
