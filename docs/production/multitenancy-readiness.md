# Estado de implementación multitenant

Actualización del cierre en `dev`: **core implementado y validado; integridad
local correcta**. El estado de producción depende además de las
comprobaciones del entorno de despliegue descritas abajo. No confundir merge,
pruebas de aplicación y autorización de puesta en producción.

## Alcance implementado

- Clínicas, membresías, roles DOCTOR/CLINIC_ADMIN/STAFF, invitaciones, selección y
  validación de contexto y administración explícita de plataforma.
- APIs organizacionales para pacientes, antecedentes, odontograma, consultas,
  agenda, imágenes, IA, consentimiento/PDF, estudios, reportes y exportaciones.
- Contacto de pacientes asignados por clínica: solo asunto/mensaje; el destinatario
  se obtiene del registro autorizado, con auditoría y respuesta controlada ante
  fallo de correo. El envío SMTP no es transaccional respecto al commit de BD.
- Recepción STAFF: directorio mínimo y agenda de su clínica; crear, reprogramar,
  completar y anular citas. No accede a antecedentes, diagnóstico ni archivos.
  No puede agendar pacientes de otra clínica ni de médicos inactivos/suspendidos.
- Consentimiento: aceptación única, identificación privada y generación de PDF
  sin recursos externos; limpieza de ambos archivos ante fallo transaccional.
- Invitaciones locales HTTP solo con DEBUG, habilitación local y host loopback;
  HTTPS obligatorio en producción. El token solo se entrega por correo.
- HTML legacy retirado. APIs clínicas globales retiradas con HTTP 410, incluidos
  métodos alternativos y sufijos de formato. El URLConf normal ya no monta la API
  de compatibilidad. El código histórico se conserva únicamente para pruebas de
  regresión aisladas, que habilitan esa compatibilidad expresamente.
- Las escrituras por servicios requieren contexto clínico autorizado. Los datos
  históricos sin clínica permanecen inaccesibles por la API normal; no se asignan
  ni eliminan automáticamente. `check_tenant_integrity` permite detectar y bloquear
  el cierre de datos con procedencia pendiente de conciliación.
- Caché por contexto, cancelación de solicitudes y descarte de respuestas
  atrasadas. Una sola membresía se valida y selecciona automáticamente; con varias
  se solicita selección. Cuentas sin clínica no abren pantallas clínicas.

## Evidencia de la implementación

- Suite completa sobre PostgreSQL temporal: **248 pruebas correctas, 0 omitidas**,
  incluyendo carreras entre recepción/médico y revocación durante espera de lock.
- Frontend: **52 pruebas correctas**; tipos y lint correctos.
- Sin migraciones de modelos pendientes en la comprobación `makemigrations`.
- Playwright: **10 escenarios verificados**. Última ejecución completa: 9 correctos
  y un fallo de selector al confundir el estado del formulario con la notificación
  de login. Se corrigió el selector y se repitió ese escenario: 1 correcto. Incluye
  flujo clínico completo, móvil, errores/reintentos, cambio de clínica y revocación,
  alta de clínicas, recuperación de credenciales y aislamiento por propietario.
- El escenario final comprobó archivos privados, consentimiento/PDF, estudio/PDF,
  inferencia IA real, exportaciones, correo, agenda STAFF y cambio de clínica.
  No fue necesario otro build: las últimas correcciones afectaron pruebas y
  configuración exclusiva de SQLite E2E (transacciones IMMEDIATE).

## Cierre de datos locales

El operador completó el build y recreó E2E. El navegador se validó contra ese
servidor aislado en 8010, con datos sintéticos separados de PostgreSQL local.

Por instrucción explícita del usuario se eliminó el paciente local #1 (sin clínica,
médico `smile`), sus dos consultas, antecedentes, odontograma y tres revisiones,
en una transacción. Se registró `LOCAL_LEGACY_PATIENT_PURGED` en auditoría. No se
reasignó ningún registro ni se eliminaron usuarios, clínicas o membresías.

Después de la eliminación, `check_tenant_integrity` terminó correctamente: todos
los contadores de procedencia y relaciones están en cero. El cierre técnico local
queda completado; las verificaciones del despliegue siguen siendo independientes.

El procedimiento y comandos están en [docker-local.md](../operations/docker-local.md).
La decisión de aislamiento de BD está en [tenant-rls.md](../database/tenant-rls.md).

## Puesta en producción

Antes de habilitar clínicas reales: verificar migración/asignación de datos del
entorno, HTTPS, correo, storage privado y permisos efectivos, roles de PostgreSQL,
backup restaurable, observabilidad y recorridos en staging. Son verificaciones
operativas que no se acreditan ejecutando pruebas locales. No se ha desplegado ni
modificado infraestructura de producción como parte de este cierre.
