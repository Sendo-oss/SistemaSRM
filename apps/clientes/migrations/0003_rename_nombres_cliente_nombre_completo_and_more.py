from django.db import migrations, models


def combinar_nombre_completo(apps, schema_editor):
    Cliente = apps.get_model("clientes", "Cliente")
    for cliente in Cliente.objects.order_by("pk"):
        nombre = (cliente.nombre_completo or "").strip()
        apellido = (getattr(cliente, "apellidos", "") or "").strip()
        combinado = f"{nombre} {apellido}".strip()
        cliente.nombre_completo = combinado or nombre or apellido
        cliente.save(update_fields=["nombre_completo"])


class Migration(migrations.Migration):

    dependencies = [
        ("clientes", "0002_alter_cliente_apellidos_alter_cliente_identificacion_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="cliente",
            old_name="nombres",
            new_name="nombre_completo",
        ),
        migrations.RenameField(
            model_name="cliente",
            old_name="correo",
            new_name="ubicacion_cliente",
        ),
        migrations.AlterField(
            model_name="cliente",
            name="nombre_completo",
            field=models.CharField(blank=True, max_length=180),
        ),
        migrations.AlterField(
            model_name="cliente",
            name="ubicacion_cliente",
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.RunPython(combinar_nombre_completo, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="cliente",
            name="apellidos",
        ),
        migrations.AlterModelOptions(
            name="cliente",
            options={
                "ordering": ["nombre_completo", "telefono"],
                "verbose_name": "Cliente",
                "verbose_name_plural": "Clientes",
            },
        ),
    ]
