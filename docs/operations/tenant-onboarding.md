# Alta de clínicas

El rol `PlatformAdmin` es explícito y se consulta en base de datos en cada solicitud; las banderas Django `is_staff` e `is_superuser` no lo conceden. Su posesión permite operaciones de plataforma, no acceso automático a expedientes clínicos. El backoffice clínico global sigue denegado mientras no exista un procedimiento excepcional autorizado.

El comando `manage_platform_admin --actor-id N --user-id N --action grant` es una simulación por defecto; `--apply` aplica el cambio. El actor indicado debe estar activo y tener asignado directamente o mediante grupo el permiso `Usuarios.manage_platform_roles`; ser superusuario no sustituye esa asignación explícita. El comando registra el actor indicado y evita revocar al último administrador de plataforma activo mediante este procedimiento. La identidad del operador del sistema operativo debe verificarse y registrarse fuera del comando: `--actor-id` por sí solo no autentica al ejecutor. La asignación inicial de este permiso requiere el procedimiento de acceso privilegiado de la organización.

La API de plataforma `POST /api/v1/backoffice/clinics/` crea clínica y una invitación de administrador inicial en una transacción. Se requieren `name`, `slug`, `initial_admin_email` y opcionalmente `status` (`INACTIVE` por defecto o `ACTIVE`). El token solo se envía por correo. Una clínica inactiva debe activarse antes de aceptar la invitación; la invitación vence a los siete días. No se crea membresía activa hasta que el destinatario la acepte.

`GET /api/v1/backoffice/clinics/` pagina clínicas. La invitación pendiente puede consultarse, revocarse y reemplazarse mediante `initial-admin/`; la emisión se bloquea si ya existe un administrador de clínica activo. Configure `TENANT_INVITATION_URL`, remitente y SMTP como se describe en tenant-invitations.md. Un error de envío revierte el alta, pero un fallo de commit después de la entrega puede dejar un enlace inválido; no hay garantía de entrega durable.

La pantalla **Administración → Clínicas** permite a un administrador de plataforma crear una clínica inactiva, activarla o suspenderla y consultar, revocar o reemplazar la invitación inicial. Los cambios de estado se confirman en la interfaz y se autorizan de nuevo en el servidor. Activar la clínica antes de que el destinatario acepte la invitación.

No se ha autorizado ni ejecutado asignación de datos clínicos históricos. La creación de una clínica no asigna pacientes.
