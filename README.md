# Sistema SRM

Sistema web base para gestion de formulacion magistral, clientes, inventario, ventas, pagos, promociones y reportes.

## Stack

- Python
- Django
- SQLite en esta primera base

## Modulos iniciales

- usuarios
- clientes
- seguimiento
- catalogo
- inventario
- proveedores
- ventas
- pagos
- promociones
- reportes
- dashboard

## Puesta en marcha

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Acceso

- Login: `http://127.0.0.1:8000/login/`
- Admin: `http://127.0.0.1:8000/admin/`
