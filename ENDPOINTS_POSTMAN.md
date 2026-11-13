# Colección Postman — Core multitenant

Importa `SmileManager.postman_collection.json` y, opcionalmente,
`SmileManager.local.postman_environment.json`. Usa Postman Desktop o el Desktop
Agent para acceder a localhost. No requiere conectar una cuenta de Postman.

## Preparación local

```bash
docker --context default compose up -d
docker --context default compose exec backend python manage.py seed_local
```

En Postman selecciona el entorno local y ejecuta **solo la carpeta 00**, en orden,
con Collection Runner. Hace login de médico, administrador de clínica y plataforma,
guarda sus tokens por separado, descubre la clínica y crea paciente, antecedentes,
odontograma, consulta y cita sintéticos. Cada petición verifica el código HTTP y
captura IDs/versiones automáticamente. Repetir 00 crea otro paciente de prueba.
Las contraseñas locales iniciales son `Admin123`; cambia la variable si las cambiaste.
Los tokens e IDs se guardan en variables de colección: no crees variables de entorno
con esos nombres porque tendrían prioridad y bloquearían la captura automática.

## Uso por módulos

Las carpetas 01–12 son un catálogo manual, no una secuencia para ejecutar completa.
Cada request incluye su rol, headers, body, prueba HTTP y requisitos. El médico usa
`tokenDoctor`, el administrador de clínica `tokenAdmin` y smile `tokenPlatform`.
Las rutas clínicas llevan `X-Clinic-ID`. Cambiar `clinicId` requiere una membresía
autorizada; ser administrador de plataforma no concede acceso a expedientes.

- Primero ejecuta 00; si caducan tokens repite solo sus tres logins.
- Antes de PUT de antecedentes/odontograma ejecuta el GET correspondiente para
  capturar la versión actual. Un conflicto de edición devuelve 409.
- Completar y cancelar son transiciones alternativas; la carpeta Agenda crea
  una segunda cita para probar cancelación.
- Cargas: selecciona archivos en Body > form-data. El estudio nuevo requiere las
  cinco fotos `antes_*`; consentimiento requiere identificación sintética.
- IA: sube imagen, analiza y consulta historial. HTTP 202 significa en curso;
  los archivos de resultado requieren SUCCEEDED. Vacía `idempotencyKey` al cambiar
  de imagen. Una clave se conserva para reintentar la misma operación.
- Los detalles de usuarios requieren crear primero el usuario de prueba. Auditoría
  e IA requieren ejecutar antes sus listas y que existan eventos/ejecuciones.
- La carpeta final archiva/desactiva datos de prueba. No ejecutar antes de los
  módulos de consulta; no borra los datos de PostgreSQL.

## Cookies, correo e invitaciones

Mantén activo el cookie jar. `session`, `refresh` y `logout` usan `smile_refresh`
del último login (smile al terminar 00). `cookieRole` indica qué token actualizar.
Las otras peticiones usan tokens Bearer independientes.

Los tokens de invitación y recuperación solo están en los correos; no se extraen
de respuestas API. Lee el correo local y copia `invitationToken` o `resetUid` y
`resetToken` en las variables de colección:

```bash
docker --context default compose exec backend ls -lt /var/lib/smilemanager/mail
docker --context default compose exec backend sh -c 'cat /var/lib/smilemanager/mail/*'
```

**Invitaciones:** HTTPS es obligatorio en producción. En desarrollo se admite
HTTP únicamente para localhost/127.0.0.1/::1 con el permiso local explícito. El
compose local funciona con Vite HTTP. El destinatario existente debe iniciar sesión
en el request de Invitaciones para obtener `tokenInvitee`.

Para probar recepción, invita una cuenta con rol STAFF, regístrala y configura
`staffUsername` y `staffPassword`. El seed conserva sus tres cuentas originales.
La carpeta 11 usa `tokenStaff` y el mismo `clinicId`; recepción solo puede consultar
el directorio mínimo de pacientes y operar citas de su clínica.

La recuperación confirma un cambio real de contraseña: ejecútala manualmente.
Los archivos sin cargar o resultados aún no generados pueden responder 404.

## Alcance

Incluye salud, autenticación, recuperación, contexto de clínicas, pacientes,
expediente, consultas, agenda, imágenes, IA, consentimientos, estudios, reportes,
exportaciones, miembros, invitaciones y backoffice administrativo. Excluye rutas
HTML retiradas, API global de compatibilidad y backoffice clínico global denegado.
HEAD y OPTIONS no se repiten. Regenera con `python3 generar_coleccion_postman.py`.

## Catálogo

### 00 · Inicio rápido — ejecutar esta carpeta en orden

| Petición                                         | Método | Ruta                                                                 |
| ------------------------------------------------ | ------ | -------------------------------------------------------------------- |
| 01 · Salud y conexión PostgreSQL                 | GET    | `{{baseUrl}}/health/ready/`                                          |
| 02 · Login Doctor                                | POST   | `{{baseUrl}}/api/v1/auth/login/`                                     |
| 03 · Login Admin                                 | POST   | `{{baseUrl}}/api/v1/auth/login/`                                     |
| 04 · Login Platform                              | POST   | `{{baseUrl}}/api/v1/auth/login/`                                     |
| 05 · Descubrir clínica del médico                | GET    | `{{baseUrl}}/api/v1/clinics/memberships/`                            |
| 06 · Validar contexto clínico                    | GET    | `{{baseUrl}}/api/v1/clinics/context/`                                |
| 07 · Crear paciente sintético (guarda patientId) | POST   | `{{baseUrl}}/api/v1/clinics/patients/`                               |
| 08 · Consultar paciente creado                   | GET    | `{{baseUrl}}/api/v1/clinics/patients/{{patientId}}/`                 |
| 09 · Leer antecedentes y versión                 | GET    | `{{baseUrl}}/api/v1/clinics/patients/{{patientId}}/medical-history/` |
| 10 · Guardar antecedentes                        | PUT    | `{{baseUrl}}/api/v1/clinics/patients/{{patientId}}/medical-history/` |
| 11 · Leer odontograma y versión                  | GET    | `{{baseUrl}}/api/v1/clinics/patients/{{patientId}}/odontogram/`      |
| 12 · Guardar odontograma                         | PUT    | `{{baseUrl}}/api/v1/clinics/patients/{{patientId}}/odontogram/`      |
| 13 · Crear consulta (guarda consultationId)      | POST   | `{{baseUrl}}/api/v1/clinics/patients/{{patientId}}/consultations/`   |
| 14 · Crear cita pendiente (guarda appointmentId) | POST   | `{{baseUrl}}/api/v1/clinics/appointments/`                           |
| 15 · Dashboard del médico                        | GET    | `{{baseUrl}}/api/v1/clinics/dashboard/`                              |
| 16 · Dashboard administrador de clínica          | GET    | `{{baseUrl}}/api/v1/clinics/admin/dashboard/`                        |
| 17 · Ver clínicas en backoffice                  | GET    | `{{baseUrl}}/api/v1/backoffice/clinics/`                             |

### 01 · Sesión y recuperación de contraseña

| Petición                                            | Método | Ruta                                              |
| --------------------------------------------------- | ------ | ------------------------------------------------- |
| session/                                            | GET    | `{{baseUrl}}/api/v1/auth/session/`                |
| refresh/                                            | POST   | `{{baseUrl}}/api/v1/auth/refresh/`                |
| Solicitar recuperación por correo                   | POST   | `{{baseUrl}}/api/v1/auth/password-reset/request/` |
| Confirmar recuperación — requiere enlace del correo | POST   | `{{baseUrl}}/api/v1/auth/password-reset/confirm/` |

### 02 · Pacientes

| Petición                  | Método | Ruta                                                             |
| ------------------------- | ------ | ---------------------------------------------------------------- |
| Listar / buscar           | GET    | `{{baseUrl}}/api/v1/clinics/patients/?search=Postman&page=1`     |
| Autocompletar             | GET    | `{{baseUrl}}/api/v1/clinics/patients/autocomplete/?term=Postman` |
| Detalle                   | GET    | `{{baseUrl}}/api/v1/clinics/patients/{{patientId}}/`             |
| Actualizar completo       | PUT    | `{{baseUrl}}/api/v1/clinics/patients/{{patientId}}/`             |
| Actualizar nombre         | PATCH  | `{{baseUrl}}/api/v1/clinics/patients/{{patientId}}/`             |
| Enviar correo al paciente | POST   | `{{baseUrl}}/api/v1/clinics/patients/{{patientId}}/email/`       |

### 03 · Expediente y consultas

| Petición                      | Método | Ruta                                                                 |
| ----------------------------- | ------ | -------------------------------------------------------------------- |
| Leer medical-history/         | GET    | `{{baseUrl}}/api/v1/clinics/patients/{{patientId}}/medical-history/` |
| Guardar medical-history/      | PUT    | `{{baseUrl}}/api/v1/clinics/patients/{{patientId}}/medical-history/` |
| Leer odontogram/              | GET    | `{{baseUrl}}/api/v1/clinics/patients/{{patientId}}/odontogram/`      |
| Guardar odontogram/           | PUT    | `{{baseUrl}}/api/v1/clinics/patients/{{patientId}}/odontogram/`      |
| Listar consultas del paciente | GET    | `{{baseUrl}}/api/v1/clinics/patients/{{patientId}}/consultations/`   |
| Detalle consulta              | GET    | `{{baseUrl}}/api/v1/clinics/consultations/{{consultationId}}/`       |

### 04 · Agenda

| Petición                      | Método | Ruta                                                                      |
| ----------------------------- | ------ | ------------------------------------------------------------------------- |
| Listar citas                  | GET    | `{{baseUrl}}/api/v1/clinics/appointments/?status=P`                       |
| Detalle cita                  | GET    | `{{baseUrl}}/api/v1/clinics/appointments/{{appointmentId}}/`              |
| Actualizar cita completa      | PUT    | `{{baseUrl}}/api/v1/clinics/appointments/{{appointmentId}}/`              |
| Actualizar observaciones      | PATCH  | `{{baseUrl}}/api/v1/clinics/appointments/{{appointmentId}}/`              |
| Completar cita pendiente      | POST   | `{{baseUrl}}/api/v1/clinics/appointments/{{appointmentId}}/complete/`     |
| Crear otra cita para cancelar | POST   | `{{baseUrl}}/api/v1/clinics/appointments/`                                |
| Cancelar segunda cita         | POST   | `{{baseUrl}}/api/v1/clinics/appointments/{{cancelAppointmentId}}/cancel/` |

### 05 · Imágenes y diagnóstico IA — seleccionar archivo

| Petición                         | Método | Ruta                                                                                   |
| -------------------------------- | ------ | -------------------------------------------------------------------------------------- |
| Subir imagen (guarda imageId)    | POST   | `{{baseUrl}}/api/v1/clinics/patients/{{patientId}}/clinical-images/`                   |
| Listar imágenes                  | GET    | `{{baseUrl}}/api/v1/clinics/patients/{{patientId}}/clinical-images/`                   |
| Detalle imagen                   | GET    | `{{baseUrl}}/api/v1/clinics/clinical-images/{{imageId}}/`                              |
| Descargar original               | GET    | `{{baseUrl}}/api/v1/clinics/clinical-images/{{imageId}}/original/file/`                |
| Diagnósticos                     | GET    | `{{baseUrl}}/api/v1/clinics/diagnostics/`                                              |
| Analizar imagen (guarda runId)   | POST   | `{{baseUrl}}/api/v1/clinics/clinical-images/{{imageId}}/analyze/`                      |
| Historial IA                     | GET    | `{{baseUrl}}/api/v1/clinics/clinical-images/{{imageId}}/analysis-runs/`                |
| Descargar resultado actual       | GET    | `{{baseUrl}}/api/v1/clinics/clinical-images/{{imageId}}/result/file/`                  |
| Descargar resultado de ejecución | GET    | `{{baseUrl}}/api/v1/clinics/clinical-images/{{imageId}}/analysis-runs/{{runId}}/file/` |

### 06 · Consentimiento y estudio comparativo — archivos manuales

| Petición                                  | Método | Ruta                                                                                                 |
| ----------------------------------------- | ------ | ---------------------------------------------------------------------------------------------------- |
| Consultar consentimiento                  | GET    | `{{baseUrl}}/api/v1/clinics/patients/{{patientId}}/consent/`                                         |
| Aceptar consentimiento con identificación | POST   | `{{baseUrl}}/api/v1/clinics/patients/{{patientId}}/consent/`                                         |
| Descargar consentimiento identity         | GET    | `{{baseUrl}}/api/v1/clinics/patients/{{patientId}}/consent/identity/file/`                           |
| Descargar consentimiento pdf              | GET    | `{{baseUrl}}/api/v1/clinics/patients/{{patientId}}/consent/pdf/file/`                                |
| Consultar estudio comparativo             | GET    | `{{baseUrl}}/api/v1/clinics/patients/{{patientId}}/comparative-study/`                               |
| Crear / actualizar estudio comparativo    | PUT    | `{{baseUrl}}/api/v1/clinics/patients/{{patientId}}/comparative-study/`                               |
| Descargar PDF del estudio                 | GET    | `{{baseUrl}}/api/v1/clinics/patients/{{patientId}}/comparative-study/pdf/`                           |
| Descargar foto antes_oclusal_superior     | GET    | `{{baseUrl}}/api/v1/clinics/patients/{{patientId}}/comparative-study/media/antes_oclusal_superior/`  |
| Descargar foto antes_lateral_izquierda    | GET    | `{{baseUrl}}/api/v1/clinics/patients/{{patientId}}/comparative-study/media/antes_lateral_izquierda/` |
| Descargar foto antes_frontal              | GET    | `{{baseUrl}}/api/v1/clinics/patients/{{patientId}}/comparative-study/media/antes_frontal/`           |
| Descargar foto antes_lateral_derecha      | GET    | `{{baseUrl}}/api/v1/clinics/patients/{{patientId}}/comparative-study/media/antes_lateral_derecha/`   |
| Descargar foto antes_oclusal_inferior     | GET    | `{{baseUrl}}/api/v1/clinics/patients/{{patientId}}/comparative-study/media/antes_oclusal_inferior/`  |
| Descargar foto despues_perfil             | GET    | `{{baseUrl}}/api/v1/clinics/patients/{{patientId}}/comparative-study/media/despues_perfil/`          |
| Descargar foto despues_semiperfil         | GET    | `{{baseUrl}}/api/v1/clinics/patients/{{patientId}}/comparative-study/media/despues_semiperfil/`      |
| Descargar foto despues_retrato_frontal    | GET    | `{{baseUrl}}/api/v1/clinics/patients/{{patientId}}/comparative-study/media/despues_retrato_frontal/` |
| Descargar foto despues_retrato_sonrisa    | GET    | `{{baseUrl}}/api/v1/clinics/patients/{{patientId}}/comparative-study/media/despues_retrato_sonrisa/` |

### 07 · Reportes y exportaciones

| Petición                      | Método | Ruta                                                      |
| ----------------------------- | ------ | --------------------------------------------------------- |
| Exportar patients XLSX        | GET    | `{{baseUrl}}/api/v1/clinics/exports/patients.xlsx`        |
| Exportar consultations XLSX   | GET    | `{{baseUrl}}/api/v1/clinics/exports/consultations.xlsx`   |
| Exportar clinical-images XLSX | GET    | `{{baseUrl}}/api/v1/clinics/exports/clinical-images.xlsx` |

### 08 · Administración de clínica

| Petición                                  | Método | Ruta                                                              |
| ----------------------------------------- | ------ | ----------------------------------------------------------------- |
| Dashboard                                 | GET    | `{{baseUrl}}/api/v1/clinics/admin/dashboard/`                     |
| Miembros (guarda membershipId del médico) | GET    | `{{baseUrl}}/api/v1/clinics/admin/memberships/`                   |
| Invitaciones                              | GET    | `{{baseUrl}}/api/v1/clinics/admin/invitations/`                   |
| Auditoría                                 | GET    | `{{baseUrl}}/api/v1/clinics/admin/audit/`                         |
| Actualizar membresía del médico           | PATCH  | `{{baseUrl}}/api/v1/clinics/memberships/{{membershipId}}/`        |
| Invitar médico por correo                 | POST   | `{{baseUrl}}/api/v1/clinics/invitations/`                         |
| Revocar invitación                        | POST   | `{{baseUrl}}/api/v1/clinics/invitations/{{invitationId}}/revoke/` |

### 09 · Invitaciones — requieren token del correo

| Petición                                | Método | Ruta                                                       |
| --------------------------------------- | ------ | ---------------------------------------------------------- |
| preview/                                | POST   | `{{baseUrl}}/api/v1/clinics/invitations/preview/`          |
| register/preview/                       | POST   | `{{baseUrl}}/api/v1/clinics/invitations/register/preview/` |
| Aceptar invitación con cuenta existente | POST   | `{{baseUrl}}/api/v1/clinics/invitations/resolve/`          |
| Registrar nueva cuenta invitada         | POST   | `{{baseUrl}}/api/v1/clinics/invitations/register/`         |
| Login destinatario existente            | POST   | `{{baseUrl}}/api/v1/auth/login/`                           |

### 10 · Backoffice de plataforma

| Petición                                                       | Método | Ruta                                                                                                      |
| -------------------------------------------------------------- | ------ | --------------------------------------------------------------------------------------------------------- |
| Dashboard                                                      | GET    | `{{baseUrl}}/api/v1/backoffice/dashboard/`                                                                |
| Clínicas                                                       | GET    | `{{baseUrl}}/api/v1/backoffice/clinics/`                                                                  |
| Usuarios                                                       | GET    | `{{baseUrl}}/api/v1/backoffice/users/`                                                                    |
| Detalle usuario                                                | GET    | `{{baseUrl}}/api/v1/backoffice/users/{{userId}}/`                                                         |
| Auditoría (guarda auditId)                                     | GET    | `{{baseUrl}}/api/v1/backoffice/audit/`                                                                    |
| Detalle evento                                                 | GET    | `{{baseUrl}}/api/v1/backoffice/audit/{{auditId}}/`                                                        |
| Ejecuciones IA globales                                        | GET    | `{{baseUrl}}/api/v1/backoffice/ai-runs/`                                                                  |
| Detalle ejecución IA                                           | GET    | `{{baseUrl}}/api/v1/backoffice/ai-runs/{{backofficeRunId}}/`                                              |
| Estado del sistema                                             | GET    | `{{baseUrl}}/api/v1/backoffice/system/`                                                                   |
| Crear usuario de prueba (guarda userId)                        | POST   | `{{baseUrl}}/api/v1/backoffice/users/create/`                                                             |
| deactivate usuario de prueba                                   | POST   | `{{baseUrl}}/api/v1/backoffice/users/{{userId}}/deactivate/`                                              |
| activate usuario de prueba                                     | POST   | `{{baseUrl}}/api/v1/backoffice/users/{{userId}}/activate/`                                                |
| Crear clínica e invitar administrador (guarda managedClinicId) | POST   | `{{baseUrl}}/api/v1/backoffice/clinics/`                                                                  |
| Cambiar estado de clínica creada                               | POST   | `{{baseUrl}}/api/v1/backoffice/clinics/{{managedClinicId}}/status/`                                       |
| Listar invitaciones iniciales                                  | GET    | `{{baseUrl}}/api/v1/backoffice/clinics/{{managedClinicId}}/initial-admin/`                                |
| Revocar invitación inicial                                     | POST   | `{{baseUrl}}/api/v1/backoffice/clinics/{{managedClinicId}}/initial-admin/{{initialInvitationId}}/revoke/` |
| Reenviar invitación inicial                                    | POST   | `{{baseUrl}}/api/v1/backoffice/clinics/{{managedClinicId}}/initial-admin/`                                |

### 11 · Recepción STAFF — requiere aceptar invitación con rol STAFF

| Petición                     | Método | Ruta                                                                             |
| ---------------------------- | ------ | -------------------------------------------------------------------------------- |
| Login recepción              | POST   | `{{baseUrl}}/api/v1/auth/login/`                                                 |
| Clínicas de recepción        | GET    | `{{baseUrl}}/api/v1/clinics/memberships/`                                        |
| Buscar pacientes para agenda | GET    | `{{baseUrl}}/api/v1/clinics/staff/patients/?term=Postman`                        |
| Listar agenda de recepción   | GET    | `{{baseUrl}}/api/v1/clinics/staff/appointments/`                                 |
| Crear cita desde recepción   | POST   | `{{baseUrl}}/api/v1/clinics/staff/appointments/`                                 |
| Detalle de cita de recepción | GET    | `{{baseUrl}}/api/v1/clinics/staff/appointments/{{staffAppointmentId}}/`          |
| Reprogramar desde recepción  | PATCH  | `{{baseUrl}}/api/v1/clinics/staff/appointments/{{staffAppointmentId}}/`          |
| complete desde recepción     | POST   | `{{baseUrl}}/api/v1/clinics/staff/appointments/{{staffAppointmentId}}/complete/` |
| cancel desde recepción       | POST   | `{{baseUrl}}/api/v1/clinics/staff/appointments/{{staffAppointmentId}}/cancel/`   |

### 12 · Operaciones finales — ejecutar manualmente

| Petición                        | Método | Ruta                                                            |
| ------------------------------- | ------ | --------------------------------------------------------------- |
| Archivar imagen                 | DELETE | `{{baseUrl}}/api/v1/clinics/clinical-images/{{imageId}}/`       |
| Desactivar paciente de prueba   | POST   | `{{baseUrl}}/api/v1/clinics/patients/{{patientId}}/deactivate/` |
| Cerrar última sesión de cookies | POST   | `{{baseUrl}}/api/v1/auth/logout/`                               |
