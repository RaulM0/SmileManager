# PostgreSQL en Neon

SmileManager conserva Django ORM y psycopg2. React llama a Django; las credenciales PostgreSQL no se exponen al navegador. Neon aloja la base de datos; `neon deploy` no publica Django ni React en Render.

## Configuración

El proyecto tiene `neon.ts` con PostgreSQL y autenticación administrada deshabilitada: se conservan los usuarios, sesiones y MFA de Django. El enlace local `.neon` y los archivos `.env`/`.env.local` están excluidos de Git.

```bash
npx --yes neon@latest init -y --org-id org-tiny-silence-59939903 --project-id damp-breeze-28751575 --branch production --services postgres
npx --yes neon@latest deploy
```

Si la CLI solicita autenticación, completarla en el navegador. Si falla, ejecutar `npx --yes neon@latest login` en una terminal interactiva y repetir el despliegue.

La CLI escribe las conexiones en `.env.local`, o `.env` si ya existe. Django carga `.env.local` y después `.env` sin reemplazar variables definidas por el entorno. Los settings de pruebas y E2E no cargan estos archivos. Usar `PYTHON_DOTENV_DISABLED=1` para desactivar su carga explícitamente.

- `DATABASE_URL`: conexión agrupada para solicitudes de la aplicación. Se deshabilitan los cursores del servidor al detectar el host `-pooler`.
- `DATABASE_URL_UNPOOLED`: conexión directa, seleccionada automáticamente por `manage.py migrate`.
- Conservar los parámetros SSL emitidos por Neon. No copiar las URLs en logs, documentación, frontend ni tickets.

## Desarrollo y verificación

Instalar las dependencias Python del proyecto con Python 3.13 y las de frontend con `npm --prefix frontend ci`.

```bash
npm run build
python scripts/verify_neon.py --migrate
```

La verificación aplica las migraciones sólo con `--migrate`, exige un host Neon y prueba conexión SQL, escritura/lectura ORM, `/health/ready/`, `/app/` e inicio de sesión HTTP. Crea un usuario sintético y lo desactiva con contraseña inutilizable al finalizar, conservando su referencia en la auditoría inmutable. Inicia y detiene un servidor WSGI local durante la prueba; no deja un despliegue web permanente. Ejecutar con settings locales y sin `THROTTLE_REDIS_URL` permite verificar PostgreSQL por separado. Los eventos de auditoría del acceso sintético pueden permanecer en la base.

Arranque interactivo:

```bash
python manage.py migrate --noinput
python manage.py runserver 127.0.0.1:8000
```

Por defecto, estos comandos usan los settings locales y la base enlazada. Para volver a PostgreSQL local sin cambiar el enlace, definir explícitamente su `DATABASE_URL` y su `DATABASE_URL_UNPOOLED` (o vaciar esta última para usar la primera).

## Render

Copiar ambas URLs a las variables privadas del servicio, junto con los secretos y servicios requeridos por los settings de producción. Mantener `FEATURE_AI_ENABLED=false` para la primera versión. La configuración no migra datos de la base local, no configura R2, Redis ni correo y no publica el backend en Render.

## Validación aislada

```bash
python -m unittest scripts.tests.test_neon_environment scripts.tests.test_docker_entrypoint
DJANGO_SETTINGS_MODULE=SmileManager.settings_test python manage.py test api.tests.test_local_email_settings --noinput
```
