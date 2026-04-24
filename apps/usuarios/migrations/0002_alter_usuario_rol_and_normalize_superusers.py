from django.db import migrations, models


def normalize_superusers(apps, schema_editor):
    Usuario = apps.get_model("usuarios", "Usuario")
    Usuario.objects.filter(is_superuser=True).exclude(rol="ADMINISTRADOR").update(
        rol="ADMINISTRADOR",
        is_staff=True,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("usuarios", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="usuario",
            name="rol",
            field=models.CharField(
                choices=[
                    ("ADMINISTRADOR", "Administrador"),
                    ("EMPLEADO", "Trabajador"),
                    ("CLIENTE", "Cliente"),
                ],
                default="EMPLEADO",
                max_length=20,
            ),
        ),
        migrations.RunPython(normalize_superusers, migrations.RunPython.noop),
    ]
