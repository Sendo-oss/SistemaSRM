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

## Despliegue gratis sugerido

Usa Render para la aplicacion Django y Supabase para PostgreSQL.

### Supabase

1. Crea un proyecto nuevo en Supabase.
2. Copia el connection string de PostgreSQL en formato URI.
3. Usalo en Render como variable `DATABASE_URL`.

### Render

1. Sube este proyecto a GitHub.
2. En Render crea un `Web Service` conectado al repositorio.
3. Usa estos comandos:

```bash
Build Command: bash build.sh
Start Command: gunicorn config.wsgi:application
```

4. Agrega estas variables de entorno:

```bash
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=tu-app.onrender.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://tu-app.onrender.com
DJANGO_SECRET_KEY=una-clave-secreta-larga
DATABASE_URL=postgresql://...
POSTGRES_SSL_REQUIRE=True
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
```

Despues del primer despliegue, crea el usuario administrador con una Render Shell:

```bash
python manage.py createsuperuser
```
