from .models import SeguimientoCliente


def seguimiento_pendiente(request):
    if not request.user.is_authenticated:
        return {"seguimientos_pendientes_total": 0}

    total = SeguimientoCliente.objects.exclude(estado=SeguimientoCliente.Estado.COMPLETADO).exclude(
        estado=SeguimientoCliente.Estado.CANCELADO
    ).count()
    return {"seguimientos_pendientes_total": total}
