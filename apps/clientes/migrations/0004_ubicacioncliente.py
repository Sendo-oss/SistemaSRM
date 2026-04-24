from django.db import migrations, models


def migrar_ubicacion_simple(apps, schema_editor):
    Cliente = apps.get_model("clientes", "Cliente")
    UbicacionCliente = apps.get_model("clientes", "UbicacionCliente")

    for cliente in Cliente.objects.order_by("pk"):
        valor = (cliente.ubicacion_cliente or "").strip()
        if valor and not UbicacionCliente.objects.filter(cliente=cliente).exists():
            UbicacionCliente.objects.create(
                cliente=cliente,
                enlace=valor,
                descripcion="Ubicacion principal",
            )


class Migration(migrations.Migration):

    dependencies = [
        ("clientes", "0003_rename_nombres_cliente_nombre_completo_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="UbicacionCliente",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("enlace", models.CharField(blank=True, max_length=500)),
                ("descripcion", models.CharField(blank=True, max_length=255)),
                ("fecha_registro", models.DateTimeField(auto_now_add=True)),
                ("cliente", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="ubicaciones", to="clientes.cliente")),
            ],
            options={
                "verbose_name": "Ubicacion del cliente",
                "verbose_name_plural": "Ubicaciones del cliente",
                "ordering": ["id"],
            },
        ),
        migrations.RunPython(migrar_ubicacion_simple, migrations.RunPython.noop),
    ]
