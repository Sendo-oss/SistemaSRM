from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Informacion adicional", {"fields": ("rol", "telefono", "direccion")}),
    )
    list_display = ("username", "first_name", "last_name", "email", "rol", "is_staff")
    list_filter = ("rol", "is_staff", "is_active")
