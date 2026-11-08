"""Generate the current multitenant core collection; no retired/compatibility routes."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
folders = {}
P = '/api/v1'
C = P + '/clinics'
B = P + '/backoffice'


def script(lines, listen='test'):
    return {'listen': listen, 'script': {'type': 'text/javascript', 'exec': lines}}


def add(group, name, method, path, body=None, *, role='Doctor', clinic=True,
        capture=None, after=(), before=(), files=(), form=None, expected=(200,), note=''):
    headers = []
    if clinic:
        headers.append({'key': 'X-Clinic-ID', 'value': '{{clinicId}}'})
    req = {'method': method, 'header': headers, 'url': '{{baseUrl}}' + path,
           'auth': {'type': 'noauth'} if role is None else {
               'type': 'bearer', 'bearer': [{'key': 'token', 'value': '{{token' + role + '}}', 'type': 'string'}]},
           'description': note or 'Ejecuta primero la carpeta 00. Usa datos sintéticos locales.'}
    if body is not None:
        headers.append({'key': 'Content-Type', 'value': 'application/json'})
        # Numeric variable placeholders stay unquoted in the transmitted JSON.
        raw = json.dumps(body, ensure_ascii=False, indent=2)
        for key in ('patientId', 'historyVersion', 'odontogramVersion'):
            raw = raw.replace('"{{' + key + '}}"', '{{' + key + '}}')
        req['body'] = {'mode': 'raw', 'raw': raw, 'options': {'raw': {'language': 'json'}}}
    if files or form is not None:
        entries = [{'key': k, 'value': str(v), 'type': 'text'} for k, v in (form or {}).items()]
        entries += [{'key': f, 'type': 'file', 'src': [], 'description': 'Selecciona un archivo sintético local.'} for f in files]
        req['body'] = {'mode': 'formdata', 'formdata': entries}
    checks = [f'pm.test("HTTP esperado {list(expected)}", () => pm.expect(pm.response.code).to.be.oneOf({list(expected)}));']
    if capture:
        checks += ['if (pm.response.code >= 200 && pm.response.code < 300) {', 'const data = pm.response.json();']
        for key, expr in capture.items():
            checks.append(f'if (({expr}) !== undefined && ({expr}) !== null) pm.collectionVariables.set("{key}", String({expr}));')
        checks.append('}')
    checks += list(after)
    item = {'name': name, 'request': req, 'event': [script(checks)]}
    if before:
        item['event'].insert(0, script(list(before), 'prerequest'))
    folders.setdefault(group, []).append(item)
    return item


setup = '00 · Inicio rápido — ejecutar esta carpeta en orden'
add(setup, '01 · Salud y conexión PostgreSQL', 'GET', '/health/ready/', role=None, clinic=False)
for index, role, user in ((2, 'Doctor', 'doctorUsername'), (3, 'Admin', 'adminUsername'), (4, 'Platform', 'platformUsername')):
    add(setup, f'0{index} · Login {role}', 'POST', P + '/auth/login/',
        {'username': '{{' + user + '}}', 'password': '{{password}}'}, role=None, clinic=False,
        capture={'token' + role: 'data.access'}, after=[
            f'if (pm.response.code === 200) pm.collectionVariables.set("cookieRole", "{role}");',
            'pm.test("Login autenticado", () => pm.expect(pm.response.json().authenticated).to.eql(true));'])
add(setup, '05 · Descubrir clínica del médico', 'GET', C + '/memberships/', clinic=False, after=[
    'const rows = pm.response.json();',
    'pm.test("El médico tiene clínica activa", () => pm.expect(rows.length).to.be.above(0));',
    'const selected = rows.find(x => x.slug === pm.variables.get("clinicSlug")) || rows[0];',
    'if (selected) pm.collectionVariables.set("clinicId", selected.id);'])
add(setup, '06 · Validar contexto clínico', 'GET', C + '/context/')
patient = {'nombre': 'Paciente Postman', 'appat': 'Prueba', 'apmat': 'Demo',
           'fecha_nacimiento': '1990-01-01', 'genero': 'F', 'telefono': '{{patientPhone}}',
           'email': 'postman.{{sampleId}}@example.test', 'estatus': 'A'}
unique = [
    'const id = pm.variables.replaceIn("{{$guid}}");',
    'pm.collectionVariables.set("sampleId", id);',
    'pm.collectionVariables.set("patientPhone", "55" + String(Date.now()).slice(-8));',
    'const date = new Date(); date.setDate(date.getDate() + 7);',
    'pm.collectionVariables.set("appointmentDate", date.toISOString().slice(0, 10));',
]
add(setup, '07 · Crear paciente sintético (guarda patientId)', 'POST', C + '/patients/', patient,
    capture={'patientId': 'data.id'}, before=unique, expected=(201,))
add(setup, '08 · Consultar paciente creado', 'GET', C + '/patients/{{patientId}}/')
add(setup, '09 · Leer antecedentes y versión', 'GET', C + '/patients/{{patientId}}/medical-history/',
    capture={'historyVersion': 'data.version'})
add(setup, '10 · Guardar antecedentes', 'PUT', C + '/patients/{{patientId}}/medical-history/',
    {'otros': 'Datos sintéticos de Postman', 'version': '{{historyVersion}}'}, capture={'historyVersion': 'data.version'})
add(setup, '11 · Leer odontograma y versión', 'GET', C + '/patients/{{patientId}}/odontogram/', capture={'odontogramVersion': 'data.version'})
odontogram = {'denticion_permanente': {'11': {'oclusal': 'caries'}}, 'denticion_decidua': {},
              'resumen': {}, 'version': '{{odontogramVersion}}'}
add(setup, '12 · Guardar odontograma', 'PUT', C + '/patients/{{patientId}}/odontogram/', odontogram, capture={'odontogramVersion': 'data.version'})
add(setup, '13 · Crear consulta (guarda consultationId)', 'POST', C + '/patients/{{patientId}}/consultations/',
    {'motivo_consulta': 'Revisión de prueba', 'diagnostico': 'Ejemplo sintético', 'tratamiento': 'Control', 'observaciones': 'Postman'},
    capture={'consultationId': 'data.id'}, expected=(201,))
appointment = {'paciente_id': '{{patientId}}', 'fecha': '{{appointmentDate}}', 'hora': '10:00',
               'motivo': 'Control Postman', 'estatus': 'P', 'observaciones': 'Datos sintéticos'}
add(setup, '14 · Crear cita pendiente (guarda appointmentId)', 'POST', C + '/appointments/', appointment,
    capture={'appointmentId': 'data.id'}, expected=(201,))
add(setup, '15 · Dashboard del médico', 'GET', C + '/dashboard/')
add(setup, '16 · Dashboard administrador de clínica', 'GET', C + '/admin/dashboard/', role='Admin')
add(setup, '17 · Ver clínicas en backoffice', 'GET', B + '/clinics/', role='Platform', clinic=False)

G = '01 · Sesión y recuperación de contraseña'
for method, path in (('GET', 'session/'), ('POST', 'refresh/')):
    add(G, path, method, P + '/auth/' + path, role=None, clinic=False, after=[
        'if (pm.response.code === 200) { const data = pm.response.json();',
        'const role = pm.collectionVariables.get("cookieRole");',
        'if (data.access && role) pm.collectionVariables.set("token" + role, data.access); }'],
        note='Usa smile_refresh del último login. Mantén habilitado el cookie jar. Tras 00, corresponde a smile; cookieRole indica qué token se actualiza.')
add(G, 'Solicitar recuperación por correo', 'POST', P + '/auth/password-reset/request/', {'email': '{{resetEmail}}'}, role=None, clinic=False)
add(G, 'Confirmar recuperación — requiere enlace del correo', 'POST', P + '/auth/password-reset/confirm/',
    {'uid': '{{resetUid}}', 'token': '{{resetToken}}', 'new_password': '{{newPassword}}', 'confirm_password': '{{newPassword}}'},
    role=None, clinic=False, note='Copia uid y token del correo local. Cambia realmente la contraseña de esa cuenta. No ejecutar automáticamente con las cuentas seed.')

G = '02 · Pacientes'
for name, method, path, body in (
    ('Listar / buscar', 'GET', '/patients/?search=Postman&page=1', None),
    ('Autocompletar', 'GET', '/patients/autocomplete/?term=Postman', None),
    ('Detalle', 'GET', '/patients/{{patientId}}/', None),
    ('Actualizar completo', 'PUT', '/patients/{{patientId}}/', patient),
    ('Actualizar nombre', 'PATCH', '/patients/{{patientId}}/', {'nombre': 'Paciente Postman actualizado'}),
    ('Enviar correo al paciente', 'POST', '/patients/{{patientId}}/email/', {'asunto': 'Control', 'mensaje': 'Recordatorio sintético de prueba'}),
):
    add(G, name, method, C + path, body)
G = '03 · Expediente y consultas'
for suffix, variable, payload in [('medical-history/', 'historyVersion', {'otros': 'Actualización sintética', 'version': '{{historyVersion}}'}), ('odontogram/', 'odontogramVersion', odontogram)]:
    add(G, 'Leer ' + suffix, 'GET', C + '/patients/{{patientId}}/' + suffix, capture={variable: 'data.version'})
    add(G, 'Guardar ' + suffix, 'PUT', C + '/patients/{{patientId}}/' + suffix, payload, capture={variable: 'data.version'}, note='Ejecuta antes el GET para obtener la versión actual; una versión obsoleta devuelve 409.')
add(G, 'Listar consultas del paciente', 'GET', C + '/patients/{{patientId}}/consultations/')
add(G, 'Detalle consulta', 'GET', C + '/consultations/{{consultationId}}/')
G = '04 · Agenda'
for name, method, path, body in (
    ('Listar citas', 'GET', '/appointments/?status=P', None),
    ('Detalle cita', 'GET', '/appointments/{{appointmentId}}/', None),
    ('Actualizar cita completa', 'PUT', '/appointments/{{appointmentId}}/', appointment),
    ('Actualizar observaciones', 'PATCH', '/appointments/{{appointmentId}}/', {'observaciones': 'Actualizada desde Postman'}),
):
    add(G, name, method, C + path, body)
add(G, 'Completar cita pendiente', 'POST', C + '/appointments/{{appointmentId}}/complete/', note='Ejecutar con una cita pendiente. Completar y cancelar son alternativas; crea otra cita para probar la otra transición.')
add(G, 'Crear otra cita para cancelar', 'POST', C + '/appointments/', {**appointment, 'hora': '11:00'}, expected=(201,), capture={'cancelAppointmentId': 'data.id'})
add(G, 'Cancelar segunda cita', 'POST', C + '/appointments/{{cancelAppointmentId}}/cancel/')
G = '05 · Imágenes y diagnóstico IA — seleccionar archivo'
add(G, 'Subir imagen (guarda imageId)', 'POST', C + '/patients/{{patientId}}/clinical-images/',
    form={'consulta_id': '{{consultationId}}', 'tipo_imagen': 'Radiografía', 'descripcion': 'Prueba sintética'}, files=('imagen',), expected=(201,), capture={'imageId': 'data.id'},
    note='Selecciona imagen real en Body > form-data > imagen. Usa un archivo sintético; consulta_id pertenece al paciente creado en 00.')
for name, path in [('Listar imágenes', '/patients/{{patientId}}/clinical-images/'), ('Detalle imagen', '/clinical-images/{{imageId}}/'), ('Descargar original', '/clinical-images/{{imageId}}/original/file/'), ('Diagnósticos', '/diagnostics/')]:
    add(G, name, 'GET', C + path)
item = add(G, 'Analizar imagen (guarda runId)', 'POST', C + '/clinical-images/{{imageId}}/analyze/', {'force': False},
           capture={'runId': 'data.run_id'}, expected=(200, 202), before=['if (!pm.collectionVariables.get("idempotencyKey")) pm.collectionVariables.set("idempotencyKey", pm.variables.replaceIn("{{$guid}}"));'],
           note='Ejecuta después de subir imagen. Modelo CPU; puede tardar. Vacía idempotencyKey al cambiar de imagen o solicitar otra ejecución. HTTP 202 indica ejecución en curso.')
item['request']['header'].append({'key': 'Idempotency-Key', 'value': '{{idempotencyKey}}'})
for name, path in [('Historial IA', '/clinical-images/{{imageId}}/analysis-runs/'), ('Descargar resultado actual', '/clinical-images/{{imageId}}/result/file/'), ('Descargar resultado de ejecución', '/clinical-images/{{imageId}}/analysis-runs/{{runId}}/file/')]:
    add(G, name, 'GET', C + path, note='Los resultados requieren una ejecución SUCCEEDED y archivo disponible. Si recibes 202 al analizar, consulta el historial hasta que termine.')
G = '06 · Consentimiento y estudio comparativo — archivos manuales'
add(G, 'Consultar consentimiento', 'GET', C + '/patients/{{patientId}}/consent/')
add(G, 'Aceptar consentimiento con identificación', 'POST', C + '/patients/{{patientId}}/consent/', form={'texto': 'Consentimiento sintético de pruebas'}, files=('archivo_ine',), note='Selecciona una identificación SINTÉTICA (imagen o PDF). Solo puede aceptarse una vez; repetir devuelve 409.')
for kind in ('identity', 'pdf'):
    add(G, 'Descargar consentimiento ' + kind, 'GET', C + '/patients/{{patientId}}/consent/' + kind + '/file/', note='Los consentimientos nuevos generan su PDF al aceptar. Los históricos sin PDF requieren conciliación.')
add(G, 'Consultar estudio comparativo', 'GET', C + '/patients/{{patientId}}/comparative-study/')
study_fields = ('antes_oclusal_superior', 'antes_lateral_izquierda', 'antes_frontal', 'antes_lateral_derecha', 'antes_oclusal_inferior', 'despues_perfil', 'despues_semiperfil', 'despues_retrato_frontal', 'despues_retrato_sonrisa')
add(G, 'Crear / actualizar estudio comparativo', 'PUT', C + '/patients/{{patientId}}/comparative-study/',
    form={'fecha_inicio': '{{appointmentDate}}', 'diagnostico': 'Prueba sintética', 'observaciones': 'Postman'}, files=study_fields[:5],
    note='Al crear son obligatorias las cinco imágenes antes_*. En actualizaciones pueden omitirse; para fotos posteriores agrega alguno de: ' + ', '.join(study_fields[5:]))
add(G, 'Descargar PDF del estudio', 'GET', C + '/patients/{{patientId}}/comparative-study/pdf/')
for field in study_fields:
    add(G, 'Descargar foto ' + field, 'GET', C + '/patients/{{patientId}}/comparative-study/media/' + field + '/', note='Requiere haber cargado esta foto en el estudio; devuelve 404 si falta.')
G = '07 · Reportes y exportaciones'
for kind in ('patients', 'consultations', 'clinical-images'):
    add(G, 'Exportar ' + kind + ' XLSX', 'GET', C + '/exports/' + kind + '.xlsx', note='Usa Send and Download para guardar el archivo XLSX.')
G = '08 · Administración de clínica'
for name, path, capture in [('Dashboard', '/admin/dashboard/', None), ('Miembros (guarda membershipId del médico)', '/admin/memberships/', {'membershipId': '(data.results.find(x => x.username === pm.variables.get("doctorUsername")) || {}).id'}), ('Invitaciones', '/admin/invitations/', None), ('Auditoría', '/admin/audit/', None)]:
    add(G, name, 'GET', C + path, role='Admin', capture=capture)
add(G, 'Actualizar membresía del médico', 'PATCH', C + '/memberships/{{membershipId}}/', {'role': 'DOCTOR', 'status': 'ACTIVE'}, role='Admin')
add(G, 'Invitar médico por correo', 'POST', C + '/invitations/', {'email': '{{invitedEmail}}', 'role': 'DOCTOR'}, role='Admin', expected=(202,), note='HTTPS en producción; HTTP loopback permitido únicamente en desarrollo. El token se entrega solo en el correo local. Para invitar recepción cambia role a STAFF.')
add(G, 'Revocar invitación', 'POST', C + '/invitations/{{invitationId}}/revoke/', role='Admin', expected=(204,), note='Copia invitationId de la lista de invitaciones. Revoca una invitación pendiente.')
G = '09 · Invitaciones — requieren token del correo'
for suffix, public in [('preview/', False), ('register/preview/', True)]:
    add(G, suffix, 'POST', C + '/invitations/' + suffix, {'token': '{{invitationToken}}'}, role=None if public else 'Invitee', clinic=False)
add(G, 'Aceptar invitación con cuenta existente', 'POST', C + '/invitations/resolve/', {'token': '{{invitationToken}}', 'action': 'accept'}, role='Invitee', clinic=False,
    note='tokenInvitee debe pertenecer a la cuenta del correo invitado. Puedes cambiar action a reject. No usar las cuentas seed salvo que sean las destinatarias.')
add(G, 'Registrar nueva cuenta invitada', 'POST', C + '/invitations/register/', {'token': '{{invitationToken}}', 'username': '{{invitedUsername}}', 'password': '{{newPassword}}'}, role=None, clinic=False, expected=(201,))
add(G, 'Login destinatario existente', 'POST', P + '/auth/login/', {'username': '{{invitedUsername}}', 'password': '{{newPassword}}'}, role=None, clinic=False, capture={'tokenInvitee': 'data.access'}, after=['if (pm.response.code === 200) pm.collectionVariables.set("cookieRole", "Invitee");'])
G = '10 · Backoffice de plataforma'
for name, path, capture in [('Dashboard', '/dashboard/', None), ('Clínicas', '/clinics/', None), ('Usuarios', '/users/', None), ('Detalle usuario', '/users/{{userId}}/', None), ('Auditoría (guarda auditId)', '/audit/', {'auditId': '(data.results[0] || {}).id'}), ('Detalle evento', '/audit/{{auditId}}/', None), ('Ejecuciones IA globales', '/ai-runs/', {'backofficeRunId': '(data.results[0] || {}).id'}), ('Detalle ejecución IA', '/ai-runs/{{backofficeRunId}}/', None), ('Estado del sistema', '/system/', None)]:
    add(G, name, 'GET', B + path, role='Platform', clinic=False, capture=capture,
        note='Ejecuta login Platform en 00. Los detalles de auditoría/IA requieren que existan registros y ejecutar antes sus listas.')
add(G, 'Crear usuario de prueba (guarda userId)', 'POST', B + '/users/create/',
    {'username': 'postman_{{sampleId}}', 'email': 'user.{{sampleId}}@example.test', 'password': '{{newPassword}}', 'backoffice_access': False},
    role='Platform', clinic=False, expected=(201,), capture={'userId': 'data.id'}, note='Ejecuta antes de Detalle usuario; repetir requiere un sampleId nuevo.')
for operation in ('deactivate', 'activate'):
    add(G, operation + ' usuario de prueba', 'POST', B + '/users/{{userId}}/' + operation + '/', role='Platform', clinic=False)
add(G, 'Crear clínica e invitar administrador (guarda managedClinicId)', 'POST', B + '/clinics/',
    {'name': 'Clínica Postman', 'slug': 'postman-{{sampleId}}', 'status': 'ACTIVE', 'initial_admin_email': '{{invitedEmail}}'},
    role='Platform', clinic=False, expected=(201,), capture={'managedClinicId': 'data.id', 'initialInvitationId': 'data.initial_admin_invitation_id'},
    note='HTTP loopback funciona en desarrollo; producción requiere HTTPS. managedClinicId se mantiene separado de clinicId para conservar el contexto del médico seed.')
add(G, 'Cambiar estado de clínica creada', 'POST', B + '/clinics/{{managedClinicId}}/status/', {'status': 'ACTIVE'}, role='Platform', clinic=False)
add(G, 'Listar invitaciones iniciales', 'GET', B + '/clinics/{{managedClinicId}}/initial-admin/', role='Platform', clinic=False)
add(G, 'Revocar invitación inicial', 'POST', B + '/clinics/{{managedClinicId}}/initial-admin/{{initialInvitationId}}/revoke/', role='Platform', clinic=False, expected=(204,))
add(G, 'Reenviar invitación inicial', 'POST', B + '/clinics/{{managedClinicId}}/initial-admin/', {'email': '{{invitedEmail}}'}, role='Platform', clinic=False, expected=(202,), capture={'initialInvitationId': 'data.invitation_id'}, note='Revoca primero la anterior; requiere clínica sin administrador activo y URL de invitación HTTPS.')
G = '11 · Recepción STAFF — requiere aceptar invitación con rol STAFF'
add(G, 'Login recepción', 'POST', P + '/auth/login/', {'username': '{{staffUsername}}', 'password': '{{staffPassword}}'}, role=None, clinic=False, capture={'tokenStaff': 'data.access'}, after=['if (pm.response.code === 200) pm.collectionVariables.set("cookieRole", "Staff");'])
add(G, 'Clínicas de recepción', 'GET', C + '/memberships/', role='Staff', clinic=False)
add(G, 'Buscar pacientes para agenda', 'GET', C + '/staff/patients/?term=Postman', role='Staff')
add(G, 'Listar agenda de recepción', 'GET', C + '/staff/appointments/', role='Staff')
add(G, 'Crear cita desde recepción', 'POST', C + '/staff/appointments/', {'paciente_id': '{{patientId}}', 'fecha': '{{appointmentDate}}', 'hora': '12:00', 'motivo': 'Recepción'}, role='Staff', expected=(201,), capture={'staffAppointmentId': 'data.id'})
add(G, 'Detalle de cita de recepción', 'GET', C + '/staff/appointments/{{staffAppointmentId}}/', role='Staff')
add(G, 'Reprogramar desde recepción', 'PATCH', C + '/staff/appointments/{{staffAppointmentId}}/', {'hora': '13:00'}, role='Staff')
for operation in ('complete', 'cancel'):
    add(G, operation + ' desde recepción', 'POST', C + '/staff/appointments/{{staffAppointmentId}}/' + operation + '/', role='Staff', note='Completar y anular son alternativas. Crea otra cita para probar la segunda transición. STAFF no accede a expedientes clínicos.')
G = '12 · Operaciones finales — ejecutar manualmente'
add(G, 'Archivar imagen', 'DELETE', C + '/clinical-images/{{imageId}}/', expected=(204,))
add(G, 'Desactivar paciente de prueba', 'POST', C + '/patients/{{patientId}}/deactivate/')
add(G, 'Cerrar última sesión de cookies', 'POST', P + '/auth/logout/', role=None, clinic=False, expected=(204,), note='Cierra la sesión del último login; los access tokens emitidos conservan su vigencia hasta expirar.', after=[
    'if (pm.response.code === 204) { const role = pm.collectionVariables.get("cookieRole"); if (role) pm.collectionVariables.unset("token" + role); pm.collectionVariables.unset("cookieRole"); }'])

variables = dict(baseUrl='http://localhost:8000', doctorUsername='medico', adminUsername='admin_clinica',
                 platformUsername='smile', password='Admin123', clinicSlug='smile-demo',
                 tokenDoctor='', tokenAdmin='', tokenPlatform='', tokenInvitee='', tokenStaff='', staffUsername='recepcion', staffPassword='PruebaLocal!987', staffAppointmentId='', cookieRole='', clinicId='',
                 patientId='', consultationId='', appointmentId='', cancelAppointmentId='',
                 historyVersion='0', odontogramVersion='0', imageId='', runId='', idempotencyKey='',
                 sampleId='', patientPhone='', appointmentDate='', membershipId='', invitationId='',
                 invitationToken='', invitedEmail='invitado@example.test', invitedUsername='invitado_postman',
                 newPassword='PruebaLocal!987', resetEmail='medico@example.test', resetUid='', resetToken='',
                 userId='', auditId='', backofficeRunId='', managedClinicId='', initialInvitationId='')
collection = {
    'info': {'name': 'SmileManager · Core multitenant · Local',
             'schema': 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json',
             'description': 'Importa y ejecuta SOLO la carpeta 00 para la prueba inicial automática. Requiere docker --context default compose up -d y python manage.py seed_local en backend. Usa cuentas locales; crea datos sintéticos. Las demás carpetas se ejecutan manualmente según sus requisitos. No ejecutar toda la colección de una vez. Ver ENDPOINTS_POSTMAN.md. No incluye HTML retirado, API de compatibilidad ni rutas clínicas globales denegadas.'},
    'variable': [{'key': k, 'value': v, 'type': 'string'} for k, v in variables.items()],
    'item': [{'name': k, 'item': v} for k, v in folders.items()],
}
(ROOT / 'SmileManager.postman_collection.json').write_text(json.dumps(collection, ensure_ascii=False, indent=2) + '\n')
environment = {'name': 'SmileManager · Local', 'values': [
    {'key': k, 'value': variables[k], 'enabled': True, 'type': 'secret' if k == 'password' else 'default'}
    for k in ('baseUrl', 'doctorUsername', 'adminUsername', 'platformUsername', 'password', 'clinicSlug')],
    '_postman_variable_scope': 'environment'}
(ROOT / 'SmileManager.local.postman_environment.json').write_text(json.dumps(environment, ensure_ascii=False, indent=2) + '\n')
intro = '''# Colección Postman — Core multitenant

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
'''
lines = [intro]
for group, items in folders.items():
    lines += ['\n### ' + group + '\n', '| Petición | Método | Ruta |', '|---|---|---|']
    lines += [f'| {i["name"]} | {i["request"]["method"]} | `{i["request"]["url"]}` |' for i in items]
(ROOT / 'ENDPOINTS_POSTMAN.md').write_text('\n'.join(lines) + '\n')
print(f'{sum(map(len, folders.values()))} peticiones en {len(folders)} carpetas')
