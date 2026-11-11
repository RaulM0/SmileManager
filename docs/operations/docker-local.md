# Backend y PostgreSQL en Docker

El frontend se ejecuta en el equipo con Vite. Docker ejecuta Django con Python 3.13, las dependencias fijadas en `requirements.txt` (PyTorch para CPU) y PostgreSQL 16. No necesita Python instalado en el equipo.

La etapa 3 añade Redis, ClamAV, un recolector de auditoría y un trabajador de seguridad. Consulta [operación y respaldo](etapa-3-local.md).

## Arranque

Desde la raíz del repositorio:

```bash
python3 scripts/setup_dev_security.py
docker compose --env-file .local-ops.env up --build -d
docker compose --env-file .local-ops.env logs -f backend
```

El backend espera a que PostgreSQL esté disponible y aplica las migraciones antes de iniciar Django. La primera construcción descarga dependencias de IA y puede tardar varios minutos.

En otra terminal, inicia tu frontend como siempre:

```bash
cd frontend
npm run dev
```

Abre `http://localhost:5173`. El proxy existente de Vite dirige `/api` y `/media` a `http://127.0.0.1:8000`. La API está en `http://localhost:8000/api/v1/` y la comprobación de disponibilidad en `http://localhost:8000/health/ready/`. El contenedor no compila ni sirve React; `/app/` requiere el frontend compilado y no es la entrada de este entorno.

Los enlaces de recuperación de contraseña e invitaciones usan Vite. Los correos se guardan en archivos dentro del contenedor, sin envío SMTP:

```bash
docker compose --env-file .local-ops.env exec backend ls -lt /var/lib/smilemanager/mail
docker compose --env-file .local-ops.env exec backend sh -c 'cat /var/lib/smilemanager/mail/*'
```

## Usuarios y clínicas

Para cargar tres cuentas de demostración y una clínica activa en la base local:

```bash
docker compose --env-file .local-ops.env exec backend python manage.py seed_local
```

Las cuentas son `smile` (administrador de plataforma con acceso al backoffice),
`admin_clinica` (administrador de Clínica Smile Demo) y `medico` (médico de esa
clínica). La contraseña inicial de las tres es `Admin123`. El comando solo admite
`SmileManager.settings_local`; puede repetirse sin duplicar registros ni cambiar
las contraseñas de cuentas existentes. No crea pacientes ni citas.

La base nueva no contiene usuarios ni clínicas. Crea una cuenta interactivamente:

```bash
docker compose --env-file .local-ops.env exec backend python manage.py createsuperuser
```

Ser superusuario no concede acceso al backoffice de plataforma. Para habilitar expresamente esa cuenta en esta base local, abre el shell:

```bash
docker compose --env-file .local-ops.env exec backend python manage.py shell
```

Sustituye el nombre por el usuario recién creado y ejecuta:

```python
from django.contrib.auth import get_user_model
from Usuarios.models import PlatformAdmin
user = get_user_model().objects.get(username='tu_usuario')
PlatformAdmin.objects.get_or_create(user=user, defaults={'is_active': True})
```

Este paso es el bootstrap manual de la base local. Para cambios operativos de roles en otros entornos usa el [procedimiento de plataforma](tenant-onboarding.md). Inicia sesión en el frontend y abre `http://localhost:5173/backoffice/clinics` para crear y activar una clínica e invitar a su administrador. Los enlaces de invitación aparecen en los correos locales. El administrador de clínica puede invitar a médicos; la cuenta de plataforma no recibe acceso clínico por ese rol.

## Persistencia y desarrollo

PostgreSQL conserva el volumen existente `smilemanager_postgres_data`. Los archivos nuevos y los correos usan los volúmenes `smilemanager_media` y `smilemanager_mail`. No se importan la base SQLite ni los archivos de `media/` del equipo.

El código se monta en modo lectura y Django recarga los cambios Python automáticamente. Después de agregar migraciones, aplícalas; si cambias dependencias, reconstruye la imagen:

```bash
docker compose --env-file .local-ops.env exec backend python manage.py migrate
docker compose --env-file .local-ops.env up --build -d backend
```

PostgreSQL también está disponible en `localhost:5433`, con base y usuario `smilemanager` y contraseña local `smilemanager_local`. Los puertos publicados solo escuchan en el equipo local.

## Validación

```bash
docker compose --env-file .local-ops.env ps
docker compose --env-file .local-ops.env exec backend python manage.py check
docker compose --env-file .local-ops.env exec backend python manage.py test --settings=SmileManager.settings_test --noinput
docker compose --env-file .local-ops.env exec backend python manage.py makemigrations --check --dry-run --settings=SmileManager.settings_test
docker compose --env-file .local-ops.env exec -e PHASE2_TEST_DATABASE_URL=postgresql://smilemanager:smilemanager_local@db:5432/postgres backend python manage.py test api.tests.test_postgres_concurrency --settings=SmileManager.settings_postgres_test --noinput
```

Las pruebas SQLite y PostgreSQL crean bases y archivos temporales separados de los datos locales. PostgreSQL utiliza una base de pruebas con nombre aleatorio.

Para detener el entorno conservando los datos:

```bash
docker compose --env-file .local-ops.env down
```

Evita `docker compose --env-file .local-ops.env down -v` si quieres conservar los volúmenes. Esta configuración usa `runserver` y credenciales locales para desarrollo; no es una configuración de despliegue.

El arranque con `service_healthy` sigue el [mecanismo de dependencias de Docker Compose](https://docs.docker.com/compose/how-tos/startup-order/).

## Cierre multitenant

Usa `--context default` si también tienes Docker Desktop: los dos motores no deben
publicar el mismo proyecto en 8000/5433. Los siguientes comandos seleccionan el motor
del sistema, donde están los datos locales de esta sesión.

El frontend normal se ejecuta con Vite en 5173. Los cambios Python se recargan desde
el repositorio; no necesitan reconstrucción si no cambiaron dependencias.

Las invitaciones HTTP funcionan únicamente en desarrollo, con habilitación local y
host localhost/127.0.0.1/::1. Producción continúa exigiendo HTTPS. Las APIs clínicas
globales (`/api/v1/patients/`, `/appointments/`, etc.) responden 410; usa `/clinics/`.

```bash
docker --context default compose exec backend python manage.py check_tenant_integrity
```

Este comando no modifica datos. Devuelve error si hay pacientes sin clínica,
procedencia inconsistente, relaciones de médicos incorrectas o consentimientos
aceptados sin PDF. Requiere conciliación explícita para datos históricos; no uses
SQL para asignar automáticamente una clínica por tener un solo médico.

### Navegador en servidor aislado, sin Python instalado en el equipo

El operador ejecuta build y arranque desde la raíz:

```bash
cd frontend
npm run build
cd ..
docker --context default compose --profile e2e up -d --force-recreate e2e
docker --context default compose --profile e2e ps
```

El servicio E2E usa SQLite temporal dentro de `/tmp` y puerto 8010. No conecta a la
base PostgreSQL local ni utiliza sus usuarios. El correo de pruebas se guarda en
`.e2e-browser-mail/` (ignorado por Git). Recrearlo reinicia sus datos sintéticos.
El frontend compilado se sirve con Django para comprobar la integración real.

Después de que E2E esté saludable:

```bash
cd frontend
SMILE_E2E_EXTERNAL=1 npx playwright test
```

Playwright usa Chromium instalado por su instalador habitual. También puede usar
un navegador Chromium ya instalado indicando su ejecutable, por ejemplo:

```bash
SMILE_E2E_EXTERNAL=1 SMILE_E2E_BROWSER=/usr/bin/brave-browser npx playwright test
```

Para repetir toda la suite desde cero, recrea primero E2E: las pruebas de
recuperación cambian contraseñas y las de acceso revocan membresías sintéticas.
El setup externo verifica que 8010 responda y limpia solo correos `.log` del
directorio reservado a la prueba. No arranca ni detiene contenedores automáticamente.

La configuración original de Playwright continúa disponible para equipos con
Python/dependencias instalados: sin `SMILE_E2E_EXTERNAL`, crea su entorno temporal
y controla su propio servidor de prueba.
