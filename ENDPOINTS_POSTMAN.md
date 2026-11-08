# Endpoints de SmileManager para Postman

La colección importable es `SmileManager.postman_collection.json`. Se generó a partir de las rutas y vistas del proyecto. Las peticiones siguientes usan las mismas variables de colección.

## Preparación

1. Importa el JSON en Postman. En Variables, configura `baseUrl`, `username`, `password` y los ID existentes. La fecha de la cita debe ser futura y el teléfono y correo del paciente deben ser únicos para el médico.
2. Ejecuta `POST /api/v1/auth/login/`. El script guarda automáticamente el access token en `accessToken`. Postman debe conservar la cookie `smile_refresh` para session, refresh y logout. En refresh también se actualiza `accessToken`.
3. Para las rutas de clínicas configura `clinicId` con el UUID y usa una cuenta con la membresía y capacidad necesarias. Algunas acciones requieren rol de administrador de clínica o de backoffice. Las rutas clínicas globales del backoffice devuelven acceso denegado por diseño.
4. Para las rutas web inicia sesión por `/sesiones/login/`: haz GET a esa página, copia la cookie `csrftoken` a `csrfToken`, y después ejecuta el POST de login. Mantén habilitado el almacenamiento de cookies de Postman. Las peticiones web modificadoras incluyen `X-CSRFToken`. La sesión web y el token API son independientes.
5. En las peticiones de archivos, selecciona archivos reales en Body > form-data. Para historial médico y odontograma primero consulta el recurso y usa su `version` actual; para uno nuevo se usa 0.

Los ID son ejemplos: deben existir y ser accesibles por el usuario. Las rutas web suelen devolver HTML o redirecciones; las exportaciones y archivos devuelven contenido binario. Envíos de correo, cambios de estado, análisis y eliminaciones producen efectos reales. Usa datos de prueba.

Los métodos documentados son los métodos funcionales de cada vista; DRF también puede responder OPTIONS y HEAD en rutas compatibles. Django Admin genera rutas adicionales dinámicamente según los modelos registrados y permisos; `/admin/` permite acceder a ellas. `/app` acepta rutas hijas de la aplicación React.

## Autenticación API

### POST /api/v1/auth/login/

```http
POST {{baseUrl}}/api/v1/auth/login/
Content-Type: application/json

{
  "username": "{{username}}",
  "password": "{{password}}"
}
```

### GET /api/v1/auth/session/

```http
GET {{baseUrl}}/api/v1/auth/session/
```

Usa la cookie smile_refresh obtenida al iniciar sesión.

### POST /api/v1/auth/refresh/

```http
POST {{baseUrl}}/api/v1/auth/refresh/
```

Usa la cookie smile_refresh obtenida al iniciar sesión.

### POST /api/v1/auth/logout/

```http
POST {{baseUrl}}/api/v1/auth/logout/
```

Usa la cookie smile_refresh obtenida al iniciar sesión.

## Salud y aplicación

### GET /health

```http
GET {{baseUrl}}/health
```

### GET /health/

```http
GET {{baseUrl}}/health/
```

### GET /health/ready

```http
GET {{baseUrl}}/health/ready
```

### GET /health/ready/

```http
GET {{baseUrl}}/health/ready/
```

### GET /

```http
GET {{baseUrl}}/
```

Redirección o página HTML. /app admite rutas hijas.

### GET /app

```http
GET {{baseUrl}}/app
```

Redirección o página HTML. /app admite rutas hijas.

### GET /app/

```http
GET {{baseUrl}}/app/
```

Redirección o página HTML. /app admite rutas hijas.

## API general

### GET /api/v1/

```http
GET {{baseUrl}}/api/v1/
Authorization: Bearer {{accessToken}}
```

Raíz del enrutador REST.

### GET /api/v1/dashboard/

```http
GET {{baseUrl}}/api/v1/dashboard/
Authorization: Bearer {{accessToken}}
```

## Pacientes API

### GET /api/v1/patients/

```http
GET {{baseUrl}}/api/v1/patients/
Authorization: Bearer {{accessToken}}
```

### POST /api/v1/patients/

```http
POST {{baseUrl}}/api/v1/patients/
Authorization: Bearer {{accessToken}}
Content-Type: application/json

{
  "nombre": "Ana",
  "appat": "Lopez",
  "apmat": "Diaz",
  "fecha_nacimiento": "1990-01-01",
  "genero": "F",
  "telefono": "1111111111",
  "email": "ana@example.com",
  "estatus": "A"
}
```

### GET /api/v1/patients/autocomplete/?term=Ana

```http
GET {{baseUrl}}/api/v1/patients/autocomplete/?term=Ana
Authorization: Bearer {{accessToken}}
```

### GET /api/v1/patients/{{patientId}}/

```http
GET {{baseUrl}}/api/v1/patients/{{patientId}}/
Authorization: Bearer {{accessToken}}
```

### PUT /api/v1/patients/{{patientId}}/

```http
PUT {{baseUrl}}/api/v1/patients/{{patientId}}/
Authorization: Bearer {{accessToken}}
Content-Type: application/json

{
  "nombre": "Ana",
  "appat": "Lopez",
  "apmat": "Diaz",
  "fecha_nacimiento": "1990-01-01",
  "genero": "F",
  "telefono": "1111111111",
  "email": "ana@example.com",
  "estatus": "A"
}
```

### PATCH /api/v1/patients/{{patientId}}/

```http
PATCH {{baseUrl}}/api/v1/patients/{{patientId}}/
Authorization: Bearer {{accessToken}}
Content-Type: application/json

{
  "nombre": "Ana María"
}
```

### POST /api/v1/patients/{{patientId}}/deactivate/

```http
POST {{baseUrl}}/api/v1/patients/{{patientId}}/deactivate/
Authorization: Bearer {{accessToken}}
```

## Expediente API

### GET /api/v1/patients/{{patientId}}/medical-history/

```http
GET {{baseUrl}}/api/v1/patients/{{patientId}}/medical-history/
Authorization: Bearer {{accessToken}}
```

### PUT /api/v1/patients/{{patientId}}/medical-history/

```http
PUT {{baseUrl}}/api/v1/patients/{{patientId}}/medical-history/
Authorization: Bearer {{accessToken}}
Content-Type: application/json

{
  "problemas_cardiacos": true,
  "alergias": "Penicilina",
  "version": 0
}
```

Para version usa el valor devuelto por GET; 0 corresponde a un registro nuevo.

### GET /api/v1/patients/{{patientId}}/consultations/

```http
GET {{baseUrl}}/api/v1/patients/{{patientId}}/consultations/
Authorization: Bearer {{accessToken}}
```

### POST /api/v1/patients/{{patientId}}/consultations/

```http
POST {{baseUrl}}/api/v1/patients/{{patientId}}/consultations/
Authorization: Bearer {{accessToken}}
Content-Type: application/json

{
  "motivo_consulta": "Control",
  "diagnostico": "Caries",
  "tratamiento": "Limpieza",
  "observaciones": "Ninguna"
}
```

### GET /api/v1/patients/{{patientId}}/clinical-images/

```http
GET {{baseUrl}}/api/v1/patients/{{patientId}}/clinical-images/
Authorization: Bearer {{accessToken}}
```

### GET /api/v1/patients/{{patientId}}/odontogram/

```http
GET {{baseUrl}}/api/v1/patients/{{patientId}}/odontogram/
Authorization: Bearer {{accessToken}}
```

### PUT /api/v1/patients/{{patientId}}/odontogram/

```http
PUT {{baseUrl}}/api/v1/patients/{{patientId}}/odontogram/
Authorization: Bearer {{accessToken}}
Content-Type: application/json

{
  "denticion_permanente": {
    "11": {
      "oclusal": "caries"
    }
  },
  "denticion_decidua": {},
  "resumen": {
    "total_dientes": 52
  },
  "version": 0
}
```

Para version usa el valor devuelto por GET; 0 corresponde a un registro nuevo.

### GET /api/v1/patients/{{patientId}}/comparative-study/

```http
GET {{baseUrl}}/api/v1/patients/{{patientId}}/comparative-study/
Authorization: Bearer {{accessToken}}
```

### GET /api/v1/patients/{{patientId}}/comparative-study/pdf/

```http
GET {{baseUrl}}/api/v1/patients/{{patientId}}/comparative-study/pdf/
Authorization: Bearer {{accessToken}}
```

### GET /api/v1/patients/{{patientId}}/comparative-study/media/{{studyField}}/

```http
GET {{baseUrl}}/api/v1/patients/{{patientId}}/comparative-study/media/{{studyField}}/
Authorization: Bearer {{accessToken}}
```

### GET /api/v1/patients/{{patientId}}/consent/

```http
GET {{baseUrl}}/api/v1/patients/{{patientId}}/consent/
Authorization: Bearer {{accessToken}}
```

### GET /api/v1/patients/{{patientId}}/consent/file/

```http
GET {{baseUrl}}/api/v1/patients/{{patientId}}/consent/file/
Authorization: Bearer {{accessToken}}
```

### GET /api/v1/patients/{{patientId}}/consent/pdf/

```http
GET {{baseUrl}}/api/v1/patients/{{patientId}}/consent/pdf/
Authorization: Bearer {{accessToken}}
```

### POST /api/v1/patients/{{patientId}}/email/

```http
POST {{baseUrl}}/api/v1/patients/{{patientId}}/email/
Authorization: Bearer {{accessToken}}
Content-Type: application/json

{
  "asunto": "Recordatorio",
  "mensaje": "Hola, le recordamos su cita."
}
```

### POST /api/v1/patients/{{patientId}}/clinical-images/

```http
POST {{baseUrl}}/api/v1/patients/{{patientId}}/clinical-images/
Authorization: Bearer {{accessToken}}
Content-Type: multipart/form-data (seleccionado por Postman)

consulta_id = {{consultationId}}
tipo_imagen = Radiografía
descripcion = Imagen clínica
imagen = [seleccionar archivo]
```

### PUT /api/v1/patients/{{patientId}}/comparative-study/

```http
PUT {{baseUrl}}/api/v1/patients/{{patientId}}/comparative-study/
Authorization: Bearer {{accessToken}}
Content-Type: multipart/form-data (seleccionado por Postman)

fecha_inicio = 2026-01-01
diagnostico = Caso
observaciones = Notas
antes_oclusal_superior = [seleccionar archivo]
antes_lateral_izquierda = [seleccionar archivo]
antes_frontal = [seleccionar archivo]
antes_lateral_derecha = [seleccionar archivo]
antes_oclusal_inferior = [seleccionar archivo]
```

Al crear requiere las cinco imágenes anteriores; selecciona archivos en Postman.

### POST /api/v1/patients/{{patientId}}/consent/

```http
POST {{baseUrl}}/api/v1/patients/{{patientId}}/consent/
Authorization: Bearer {{accessToken}}
Content-Type: multipart/form-data (seleccionado por Postman)

texto = Acepto el consentimiento
archivo_ine = [seleccionar archivo]
```

### GET /api/v1/consultations/{{consultationId}}/

```http
GET {{baseUrl}}/api/v1/consultations/{{consultationId}}/
Authorization: Bearer {{accessToken}}
```

## Citas API

### GET /api/v1/appointments/

```http
GET {{baseUrl}}/api/v1/appointments/
Authorization: Bearer {{accessToken}}
```

### POST /api/v1/appointments/

```http
POST {{baseUrl}}/api/v1/appointments/
Authorization: Bearer {{accessToken}}
Content-Type: application/json

{
  "paciente_id": "{{patientId}}",
  "fecha": "{{appointmentDate}}",
  "hora": "10:00",
  "motivo": "Control",
  "estatus": "P",
  "observaciones": "Ninguna"
}
```

### GET /api/v1/appointments/{{appointmentId}}/

```http
GET {{baseUrl}}/api/v1/appointments/{{appointmentId}}/
Authorization: Bearer {{accessToken}}
```

### PUT /api/v1/appointments/{{appointmentId}}/

```http
PUT {{baseUrl}}/api/v1/appointments/{{appointmentId}}/
Authorization: Bearer {{accessToken}}
Content-Type: application/json

{
  "paciente_id": "{{patientId}}",
  "fecha": "{{appointmentDate}}",
  "hora": "10:00",
  "motivo": "Control",
  "estatus": "P",
  "observaciones": "Ninguna"
}
```

### PATCH /api/v1/appointments/{{appointmentId}}/

```http
PATCH {{baseUrl}}/api/v1/appointments/{{appointmentId}}/
Authorization: Bearer {{accessToken}}
Content-Type: application/json

{
  "motivo": "Revisión"
}
```

### POST /api/v1/appointments/{{appointmentId}}/complete/

```http
POST {{baseUrl}}/api/v1/appointments/{{appointmentId}}/complete/
Authorization: Bearer {{accessToken}}
```

### POST /api/v1/appointments/{{appointmentId}}/cancel/

```http
POST {{baseUrl}}/api/v1/appointments/{{appointmentId}}/cancel/
Authorization: Bearer {{accessToken}}
```

## Imágenes, diagnóstico y exportación API

### GET /api/v1/clinical-images/{{imageId}}/

```http
GET {{baseUrl}}/api/v1/clinical-images/{{imageId}}/
Authorization: Bearer {{accessToken}}
```

### DELETE /api/v1/clinical-images/{{imageId}}/

```http
DELETE {{baseUrl}}/api/v1/clinical-images/{{imageId}}/
Authorization: Bearer {{accessToken}}
```

### GET /api/v1/clinical-images/{{imageId}}/file/

```http
GET {{baseUrl}}/api/v1/clinical-images/{{imageId}}/file/
Authorization: Bearer {{accessToken}}
```

### GET /api/v1/clinical-images/{{imageId}}/result-file/

```http
GET {{baseUrl}}/api/v1/clinical-images/{{imageId}}/result-file/
Authorization: Bearer {{accessToken}}
```

### POST /api/v1/clinical-images/{{imageId}}/analyze/

```http
POST {{baseUrl}}/api/v1/clinical-images/{{imageId}}/analyze/
Authorization: Bearer {{accessToken}}
Content-Type: application/json

{
  "force": false
}
```

### GET /api/v1/clinical-images/{{imageId}}/analysis-runs/

```http
GET {{baseUrl}}/api/v1/clinical-images/{{imageId}}/analysis-runs/
Authorization: Bearer {{accessToken}}
```

### GET /api/v1/clinical-images/{{imageId}}/analysis-runs/{{runId}}/file/

```http
GET {{baseUrl}}/api/v1/clinical-images/{{imageId}}/analysis-runs/{{runId}}/file/
Authorization: Bearer {{accessToken}}
```

### GET /api/v1/diagnostics/

```http
GET {{baseUrl}}/api/v1/diagnostics/
Authorization: Bearer {{accessToken}}
```

### GET /api/v1/exports/patients.xlsx

```http
GET {{baseUrl}}/api/v1/exports/patients.xlsx
Authorization: Bearer {{accessToken}}
```

### GET /api/v1/exports/consultations.xlsx

```http
GET {{baseUrl}}/api/v1/exports/consultations.xlsx
Authorization: Bearer {{accessToken}}
```

### GET /api/v1/exports/clinical-images.xlsx

```http
GET {{baseUrl}}/api/v1/exports/clinical-images.xlsx
Authorization: Bearer {{accessToken}}
```

## Clínicas API

### GET /api/v1/clinics/memberships/

```http
GET {{baseUrl}}/api/v1/clinics/memberships/
Authorization: Bearer {{accessToken}}
```

### GET /api/v1/clinics/context/

```http
GET {{baseUrl}}/api/v1/clinics/context/
Authorization: Bearer {{accessToken}}
X-Clinic-ID: {{clinicId}}
```

### PATCH /api/v1/clinics/memberships/{{membershipId}}/

```http
PATCH {{baseUrl}}/api/v1/clinics/memberships/{{membershipId}}/
Authorization: Bearer {{accessToken}}
X-Clinic-ID: {{clinicId}}
Content-Type: application/json

{
  "role": "DOCTOR"
}
```

### GET /api/v1/clinics/patients/

```http
GET {{baseUrl}}/api/v1/clinics/patients/
Authorization: Bearer {{accessToken}}
X-Clinic-ID: {{clinicId}}
```

### POST /api/v1/clinics/patients/

```http
POST {{baseUrl}}/api/v1/clinics/patients/
Authorization: Bearer {{accessToken}}
X-Clinic-ID: {{clinicId}}
Content-Type: application/json

{
  "nombre": "Ana",
  "appat": "Lopez",
  "apmat": "Diaz",
  "fecha_nacimiento": "1990-01-01",
  "genero": "F",
  "telefono": "1111111111",
  "email": "ana@example.com",
  "estatus": "A"
}
```

### GET /api/v1/clinics/patients/{{patientId}}/

```http
GET {{baseUrl}}/api/v1/clinics/patients/{{patientId}}/
Authorization: Bearer {{accessToken}}
X-Clinic-ID: {{clinicId}}
```

### PUT /api/v1/clinics/patients/{{patientId}}/

```http
PUT {{baseUrl}}/api/v1/clinics/patients/{{patientId}}/
Authorization: Bearer {{accessToken}}
X-Clinic-ID: {{clinicId}}
Content-Type: application/json

{
  "nombre": "Ana",
  "appat": "Lopez",
  "apmat": "Diaz",
  "fecha_nacimiento": "1990-01-01",
  "genero": "F",
  "telefono": "1111111111",
  "email": "ana@example.com",
  "estatus": "A"
}
```

### PATCH /api/v1/clinics/patients/{{patientId}}/

```http
PATCH {{baseUrl}}/api/v1/clinics/patients/{{patientId}}/
Authorization: Bearer {{accessToken}}
X-Clinic-ID: {{clinicId}}
Content-Type: application/json

{
  "nombre": "Ana María"
}
```

### POST /api/v1/clinics/invitations/

```http
POST {{baseUrl}}/api/v1/clinics/invitations/
Authorization: Bearer {{accessToken}}
X-Clinic-ID: {{clinicId}}
Content-Type: application/json

{
  "email": "invitado@example.com",
  "role": "DOCTOR"
}
```

### POST /api/v1/clinics/invitations/preview/

```http
POST {{baseUrl}}/api/v1/clinics/invitations/preview/
Authorization: Bearer {{accessToken}}
Content-Type: application/json

{
  "token": "{{invitationToken}}"
}
```

### POST /api/v1/clinics/invitations/resolve/

```http
POST {{baseUrl}}/api/v1/clinics/invitations/resolve/
Authorization: Bearer {{accessToken}}
Content-Type: application/json

{
  "token": "{{invitationToken}}",
  "action": "accept"
}
```

### POST /api/v1/clinics/invitations/register/preview/

```http
POST {{baseUrl}}/api/v1/clinics/invitations/register/preview/
Content-Type: application/json

{
  "token": "{{invitationToken}}"
}
```

### POST /api/v1/clinics/invitations/register/

```http
POST {{baseUrl}}/api/v1/clinics/invitations/register/
Content-Type: application/json

{
  "token": "{{invitationToken}}",
  "username": "nuevo_usuario",
  "password": "Unique$Password987"
}
```

### POST /api/v1/clinics/invitations/{{invitationId}}/revoke/

```http
POST {{baseUrl}}/api/v1/clinics/invitations/{{invitationId}}/revoke/
Authorization: Bearer {{accessToken}}
X-Clinic-ID: {{clinicId}}
```

## Backoffice API

### GET /api/v1/backoffice/dashboard/

```http
GET {{baseUrl}}/api/v1/backoffice/dashboard/
Authorization: Bearer {{accessToken}}
```

Requiere permisos de backoffice.

### GET /api/v1/backoffice/users/

```http
GET {{baseUrl}}/api/v1/backoffice/users/
Authorization: Bearer {{accessToken}}
```

Requiere permisos de backoffice.

### GET /api/v1/backoffice/users/{{userId}}/

```http
GET {{baseUrl}}/api/v1/backoffice/users/{{userId}}/
Authorization: Bearer {{accessToken}}
```

Requiere permisos de backoffice.

### GET /api/v1/backoffice/audit/

```http
GET {{baseUrl}}/api/v1/backoffice/audit/
Authorization: Bearer {{accessToken}}
```

Requiere permisos de backoffice.

### GET /api/v1/backoffice/audit/{{auditId}}/

```http
GET {{baseUrl}}/api/v1/backoffice/audit/{{auditId}}/
Authorization: Bearer {{accessToken}}
```

Requiere permisos de backoffice.

### GET /api/v1/backoffice/ai-runs/

```http
GET {{baseUrl}}/api/v1/backoffice/ai-runs/
Authorization: Bearer {{accessToken}}
```

Requiere permisos de backoffice.

### GET /api/v1/backoffice/ai-runs/{{runId}}/

```http
GET {{baseUrl}}/api/v1/backoffice/ai-runs/{{runId}}/
Authorization: Bearer {{accessToken}}
```

Requiere permisos de backoffice.

### GET /api/v1/backoffice/system/

```http
GET {{baseUrl}}/api/v1/backoffice/system/
Authorization: Bearer {{accessToken}}
```

Requiere permisos de backoffice.

### GET /api/v1/backoffice/patients/

```http
GET {{baseUrl}}/api/v1/backoffice/patients/
Authorization: Bearer {{accessToken}}
```

Las rutas clínicas globales están deshabilitadas por la política actual.

### GET /api/v1/backoffice/patients/{{patientId}}/

```http
GET {{baseUrl}}/api/v1/backoffice/patients/{{patientId}}/
Authorization: Bearer {{accessToken}}
```

Las rutas clínicas globales están deshabilitadas por la política actual.

### GET /api/v1/backoffice/patients/{{patientId}}/{{section}}/

```http
GET {{baseUrl}}/api/v1/backoffice/patients/{{patientId}}/{{section}}/
Authorization: Bearer {{accessToken}}
```

Las rutas clínicas globales están deshabilitadas por la política actual.

### GET /api/v1/backoffice/appointments/

```http
GET {{baseUrl}}/api/v1/backoffice/appointments/
Authorization: Bearer {{accessToken}}
```

Las rutas clínicas globales están deshabilitadas por la política actual.

### GET /api/v1/backoffice/appointments/{{appointmentId}}/

```http
GET {{baseUrl}}/api/v1/backoffice/appointments/{{appointmentId}}/
Authorization: Bearer {{accessToken}}
```

Las rutas clínicas globales están deshabilitadas por la política actual.

### POST /api/v1/backoffice/users/{{userId}}/activate/

```http
POST {{baseUrl}}/api/v1/backoffice/users/{{userId}}/activate/
Authorization: Bearer {{accessToken}}
```

Requiere permisos de backoffice.

### POST /api/v1/backoffice/users/{{userId}}/deactivate/

```http
POST {{baseUrl}}/api/v1/backoffice/users/{{userId}}/deactivate/
Authorization: Bearer {{accessToken}}
```

Requiere permisos de backoffice.

## Web Django - Sesión y páginas

### GET /sesiones/login/

```http
GET {{baseUrl}}/sesiones/login/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /home/

```http
GET {{baseUrl}}/home/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /home/aviso-privacidad/

```http
GET {{baseUrl}}/home/aviso-privacidad/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /admin/

```http
GET {{baseUrl}}/admin/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

## Web Django - Citas

### GET /menu_citas/

```http
GET {{baseUrl}}/menu_citas/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /menu_citas/nueva_cita/

```http
GET {{baseUrl}}/menu_citas/nueva_cita/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /menu_citas/registrar_cita/{{patientId}}/

```http
GET {{baseUrl}}/menu_citas/registrar_cita/{{patientId}}/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /menu_citas/buscar_cita/?buscador=Ana

```http
GET {{baseUrl}}/menu_citas/buscar_cita/?buscador=Ana
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /menu_citas/editar_cita/{{appointmentId}}/

```http
GET {{baseUrl}}/menu_citas/editar_cita/{{appointmentId}}/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /menu_citas/citas_pendientes/

```http
GET {{baseUrl}}/menu_citas/citas_pendientes/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /menu_citas/citas_completadas/

```http
GET {{baseUrl}}/menu_citas/citas_completadas/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /menu_citas/citas_canceladas/

```http
GET {{baseUrl}}/menu_citas/citas_canceladas/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /menu_citas/detalle_cita/{{appointmentId}}/

```http
GET {{baseUrl}}/menu_citas/detalle_cita/{{appointmentId}}/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

## Web Django - Pacientes

### GET /registroPacientes/

```http
GET {{baseUrl}}/registroPacientes/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /registroPacientes/registrar_pacientes/

```http
GET {{baseUrl}}/registroPacientes/registrar_pacientes/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /registroPacientes/todosPacientes

```http
GET {{baseUrl}}/registroPacientes/todosPacientes
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /registroPacientes/buscar_pacientes/?q=Ana

```http
GET {{baseUrl}}/registroPacientes/buscar_pacientes/?q=Ana
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /registroPacientes/ver_paciente/{{patientId}}/

```http
GET {{baseUrl}}/registroPacientes/ver_paciente/{{patientId}}/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /registroPacientes/editar_paciente/{{patientId}}/

```http
GET {{baseUrl}}/registroPacientes/editar_paciente/{{patientId}}/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /registroPacientes/menu_historial/

```http
GET {{baseUrl}}/registroPacientes/menu_historial/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /registroPacientes/buscar_pacientes_ajax/?term=Ana

```http
GET {{baseUrl}}/registroPacientes/buscar_pacientes_ajax/?term=Ana
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /registroPacientes/antecedentes/{{patientId}}/

```http
GET {{baseUrl}}/registroPacientes/antecedentes/{{patientId}}/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /registroPacientes/consultas/{{patientId}}/

```http
GET {{baseUrl}}/registroPacientes/consultas/{{patientId}}/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /registroPacientes/receta/{{consultationId}}/

```http
GET {{baseUrl}}/registroPacientes/receta/{{consultationId}}/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /registroPacientes/historial_consultas/{{patientId}}/

```http
GET {{baseUrl}}/registroPacientes/historial_consultas/{{patientId}}/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /registroPacientes/imagenes_clinicas/{{patientId}}/

```http
GET {{baseUrl}}/registroPacientes/imagenes_clinicas/{{patientId}}/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /registroPacientes/cargar_imagen/{{patientId}}/

```http
GET {{baseUrl}}/registroPacientes/cargar_imagen/{{patientId}}/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /registroPacientes/buscar_imagen/{{patientId}}/

```http
GET {{baseUrl}}/registroPacientes/buscar_imagen/{{patientId}}/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /registroPacientes/historial_imagenes/{{patientId}}/

```http
GET {{baseUrl}}/registroPacientes/historial_imagenes/{{patientId}}/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /registroPacientes/exportar_datos/

```http
GET {{baseUrl}}/registroPacientes/exportar_datos/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /registroPacientes/exportar_pacientes/

```http
GET {{baseUrl}}/registroPacientes/exportar_pacientes/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /registroPacientes/exportar_consultas/

```http
GET {{baseUrl}}/registroPacientes/exportar_consultas/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /registroPacientes/exportar_imagenes/

```http
GET {{baseUrl}}/registroPacientes/exportar_imagenes/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /registroPacientes/contactar_pacientes/

```http
GET {{baseUrl}}/registroPacientes/contactar_pacientes/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /registroPacientes/contacto/{{patientId}}/

```http
GET {{baseUrl}}/registroPacientes/contacto/{{patientId}}/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /registroPacientes/enviar_mensaje/

```http
GET {{baseUrl}}/registroPacientes/enviar_mensaje/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /registroPacientes/odontograma/{{patientId}}/

```http
GET {{baseUrl}}/registroPacientes/odontograma/{{patientId}}/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /registroPacientes/progreso/{{patientId}}/

```http
GET {{baseUrl}}/registroPacientes/progreso/{{patientId}}/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /registroPacientes/estudio/{{patientId}}/

```http
GET {{baseUrl}}/registroPacientes/estudio/{{patientId}}/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /registroPacientes/estudio/{{patientId}}/visualizar/

```http
GET {{baseUrl}}/registroPacientes/estudio/{{patientId}}/visualizar/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /registroPacientes/estudio/{{patientId}}/descargar-pdf/

```http
GET {{baseUrl}}/registroPacientes/estudio/{{patientId}}/descargar-pdf/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /registroPacientes/consentimiento/{{patientId}}/

```http
GET {{baseUrl}}/registroPacientes/consentimiento/{{patientId}}/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /registroPacientes/archivos/{{fileKind}}/{{resourceId}}/{{fileField}}/

```http
GET {{baseUrl}}/registroPacientes/archivos/{{fileKind}}/{{resourceId}}/{{fileField}}/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

## Web Django - Diagnósticos

### GET /diagnosticos/

```http
GET {{baseUrl}}/diagnosticos/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

### GET /diagnosticos/resultados/{{imageId}}/

```http
GET {{baseUrl}}/diagnosticos/resultados/{{imageId}}/
```

Vista web: utiliza sesión Django; puede responder HTML, redirección o archivo.

## Web Django - Formularios

### POST /sesiones/login/

```http
POST {{baseUrl}}/sesiones/login/
X-CSRFToken: {{csrfToken}}
Content-Type: application/x-www-form-urlencoded

username = {{username}}
password = {{password}}
```

Requiere cookie de sesión y CSRF; login solo necesita CSRF.

### POST /sesiones/logout/

```http
POST {{baseUrl}}/sesiones/logout/
X-CSRFToken: {{csrfToken}}
Content-Type: application/x-www-form-urlencoded

```

Requiere cookie de sesión y CSRF; login solo necesita CSRF.

### POST /menu_citas/registrar_cita/{{patientId}}/

```http
POST {{baseUrl}}/menu_citas/registrar_cita/{{patientId}}/
X-CSRFToken: {{csrfToken}}
Content-Type: application/x-www-form-urlencoded

fecha = {{appointmentDate}}
hora = 10:00
motivo = Control
estatus = P
observaciones = Ninguna
```

Requiere cookie de sesión y CSRF; login solo necesita CSRF.

### POST /menu_citas/editar_cita/{{appointmentId}}/

```http
POST {{baseUrl}}/menu_citas/editar_cita/{{appointmentId}}/
X-CSRFToken: {{csrfToken}}
Content-Type: application/x-www-form-urlencoded

fecha = {{appointmentDate}}
hora = 10:00
motivo = Control
estatus = P
observaciones = Ninguna
```

Requiere cookie de sesión y CSRF; login solo necesita CSRF.

### POST /menu_citas/confirmar_asistencia/{{appointmentId}}/

```http
POST {{baseUrl}}/menu_citas/confirmar_asistencia/{{appointmentId}}/
X-CSRFToken: {{csrfToken}}
Content-Type: application/x-www-form-urlencoded

```

Requiere cookie de sesión y CSRF; login solo necesita CSRF.

### POST /menu_citas/cancelar_cita/{{appointmentId}}/

```http
POST {{baseUrl}}/menu_citas/cancelar_cita/{{appointmentId}}/
X-CSRFToken: {{csrfToken}}
Content-Type: application/x-www-form-urlencoded

```

Requiere cookie de sesión y CSRF; login solo necesita CSRF.

### POST /registroPacientes/registrar_pacientes/

```http
POST {{baseUrl}}/registroPacientes/registrar_pacientes/
X-CSRFToken: {{csrfToken}}
Content-Type: application/x-www-form-urlencoded

nombre = Ana
appat = Lopez
apmat = Diaz
fecha_nacimiento = 1990-01-01
genero = F
telefono = 1111111111
email = ana@example.com
estatus = A
```

Requiere cookie de sesión y CSRF; login solo necesita CSRF.

### POST /registroPacientes/editar_paciente/{{patientId}}/

```http
POST {{baseUrl}}/registroPacientes/editar_paciente/{{patientId}}/
X-CSRFToken: {{csrfToken}}
Content-Type: application/x-www-form-urlencoded

nombre = Ana María
```

Requiere cookie de sesión y CSRF; login solo necesita CSRF.

### POST /registroPacientes/eliminar_paciente/{{patientId}}/

```http
POST {{baseUrl}}/registroPacientes/eliminar_paciente/{{patientId}}/
X-CSRFToken: {{csrfToken}}
Content-Type: application/x-www-form-urlencoded

```

Requiere cookie de sesión y CSRF; login solo necesita CSRF.

### POST /registroPacientes/antecedentes/{{patientId}}/

```http
POST {{baseUrl}}/registroPacientes/antecedentes/{{patientId}}/
X-CSRFToken: {{csrfToken}}
Content-Type: application/x-www-form-urlencoded

problemas_cardiacos = True
alergias_txt = Penicilina
version = 0
```

Requiere cookie de sesión y CSRF; login solo necesita CSRF.

### POST /registroPacientes/consultas/{{patientId}}/

```http
POST {{baseUrl}}/registroPacientes/consultas/{{patientId}}/
X-CSRFToken: {{csrfToken}}
Content-Type: application/x-www-form-urlencoded

motivo_consulta = Control
diagnostico = Caries
tratamiento = Limpieza
observaciones = Ninguna
```

Requiere cookie de sesión y CSRF; login solo necesita CSRF.

### POST /registroPacientes/eliminar_imagen/{{imageId}}/

```http
POST {{baseUrl}}/registroPacientes/eliminar_imagen/{{imageId}}/
X-CSRFToken: {{csrfToken}}
Content-Type: application/x-www-form-urlencoded

```

Requiere cookie de sesión y CSRF; login solo necesita CSRF.

### POST /registroPacientes/enviar_mensaje/

```http
POST {{baseUrl}}/registroPacientes/enviar_mensaje/
X-CSRFToken: {{csrfToken}}
Content-Type: application/x-www-form-urlencoded

paciente_id = {{patientId}}
asunto = Recordatorio
mensaje = Hola, le recordamos su cita.
```

Requiere cookie de sesión y CSRF; login solo necesita CSRF.

### POST /diagnosticos/resultados/{{imageId}}/

```http
POST {{baseUrl}}/diagnosticos/resultados/{{imageId}}/
X-CSRFToken: {{csrfToken}}
Content-Type: application/x-www-form-urlencoded

force = false
```

Requiere cookie de sesión y CSRF; login solo necesita CSRF.

### POST /registroPacientes/odontograma/guardar/{{patientId}}/

```http
POST {{baseUrl}}/registroPacientes/odontograma/guardar/{{patientId}}/
X-CSRFToken: {{csrfToken}}
Content-Type: application/json

{
  "denticion_permanente": {
    "11": {
      "oclusal": "caries"
    }
  },
  "denticion_decidua": {},
  "resumen": {
    "total_dientes": 52
  },
  "version": 0
}
```

### POST /registroPacientes/cargar_imagen/{{patientId}}/

```http
POST {{baseUrl}}/registroPacientes/cargar_imagen/{{patientId}}/
X-CSRFToken: {{csrfToken}}
Content-Type: multipart/form-data (seleccionado por Postman)

consulta_id = {{consultationId}}
tipo = Radiografía
descripcion = Imagen clínica
archivo = [seleccionar archivo]
```

### POST /registroPacientes/estudio/{{patientId}}/

```http
POST {{baseUrl}}/registroPacientes/estudio/{{patientId}}/
X-CSRFToken: {{csrfToken}}
Content-Type: multipart/form-data (seleccionado por Postman)

fecha_inicio = 2026-01-01
diagnostico = Caso
observaciones = Notas
antes_oclusal_superior = [seleccionar archivo]
antes_lateral_izquierda = [seleccionar archivo]
antes_frontal = [seleccionar archivo]
antes_lateral_derecha = [seleccionar archivo]
antes_oclusal_inferior = [seleccionar archivo]
```

### POST /registroPacientes/consentimiento/{{patientId}}/

```http
POST {{baseUrl}}/registroPacientes/consentimiento/{{patientId}}/
X-CSRFToken: {{csrfToken}}
Content-Type: multipart/form-data (seleccionado por Postman)

texto = Acepto
archivo_ine = [seleccionar archivo]
```
