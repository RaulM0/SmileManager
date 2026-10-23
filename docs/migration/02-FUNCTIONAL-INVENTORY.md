# Inventario funcional

Los permisos indicados como **médico propietario** significan usuario autenticado y objeto enlazado a ese usuario. Salvo indicación, los errores son 404 por objeto ajeno/inexistente y validación con mensaje. Estado inicial de todo el inventario: `ANALYZED`.

## Sesión y navegación

### FUNC-001 — Iniciar sesión
- Usuario/rol: anónimo. URL/View/Template/Form: `/sesiones/login/`; `login_view`; `sesiones/login.html`; `LoginForm`.
- Models/JS: `auth.User`, sesión; validación HTML y toggle visual. Permiso: público.
- Reglas/efectos: autentica username/password, crea sesión, respeta `next`, redirige autenticado a home; credenciales inválidas muestran mensaje.
- Dependencias/migración: Django auth + CSRF; `POST /api/v1/auth/login/`; `LoginPage`; sesión/cookie. Estado: VERIFIED; pruebas backend, componente y E2E pasan.

### FUNC-002 — Cerrar sesión
- Usuario/rol: autenticado. URL/View/Template/Form: `/sesiones/logout/`; `logout_view`; enlaces de layout; sin form.
- Reglas/efectos: destruye sesión y redirige a login. Riesgo legacy: GET muta estado.
- Migración: `POST /api/v1/auth/logout/`; acción de `AppLayout`. Estado: VERIFIED; API y logout E2E pasan.

### FUNC-003 — Obtener sesión/perfil y layout
- Usuario: autenticado. Legacy: `base.html`, `request.user`, `user.perfil`; señal `crear_o_guardar_perfil`.
- Reglas: cada User debe tener Perfil; navbar móvil/escritorio y nombre/clínica condicionales.
- Migración: `GET /api/v1/auth/session/`; `AuthContext`, `AppLayout`, `ProtectedRoute`. Estado: VERIFIED; API, rutas protegidas y E2E responsive pasan.

### FUNC-004 — Panel principal
- URL/View/Template: `/home/`; `Home.home`; `home/home.html`. Models: Paciente, Cita.
- Reglas: conteo de pacientes del médico, citas de hoy y futuras; accesos rápidos y tablas. Propietario.
- Migración: `GET /api/v1/dashboard/`; `DashboardPage`. Estado: VERIFIED; API y carga E2E pasan.

### FUNC-005 — Aviso de privacidad
- URL/View/Template: `/home/aviso-privacidad/`; `aviso_privacidad`; template homónimo. Sin datos.
- Migración: contenido React estático; `PrivacyPage`. Estado: VERIFIED; navegación E2E pasa.

## Pacientes

### FUNC-006 — Menú de pacientes
- URL/View/Template: `/registroPacientes/`; `menuPacientes`; `pacientes/menuPacientes.html`.
- Comportamiento: accesos a listar, crear, buscar, historial, exportar y contactar. Migración: `PatientsHubPage`. Estado: VERIFIED; navegación E2E pasa.

### FUNC-007 — Registrar paciente
- URL/View/Template/Form: `/registroPacientes/registrar_pacientes/`; `registrar_paciente`; `registroPacientes.html`; POST manual.
- Models/validación: Paciente; nombre/apellidos/email a mayúsculas; fecha obligatoria YYYY-MM-DD; teléfono y email únicos por médico; género M/F; teléfono HTML máx. 10.
- Efectos/errores: crea paciente del usuario; mensajes específicos; integridad también protegida por constraints.
- Migración: `POST /api/v1/patients/`; `PatientCreatePage`; serializer + servicio. Estado: VERIFIED; API y E2E pasan.

### FUNC-008 — Listar pacientes
- URL/View/Template: `/registroPacientes/todosPacientes`; `todos_los_pacientes`; `todosPacientes.html`.
- Regla: sólo propios, orden por apellido paterno. Migración: `GET /api/v1/patients/`; `PatientListPage`. Estado: VERIFIED; API y componente compartido E2E pasan.

### FUNC-009 — Buscar y paginar pacientes
- URL/View/Template: `/registroPacientes/buscar_pacientes/?q=&page=`; `buscar_pacientes`; `buscar_pacientes.html`.
- Regla: busca insensible en nombre, apellidos, nombre completo, teléfono o email; 10/página; propios.
- Migración: `GET /api/v1/patients/?search=&page=`; `PatientListPage` en modo búsqueda. Estado: VERIFIED; búsqueda E2E pasa.

### FUNC-010 — Ver paciente
- URL/View/Template: `/registroPacientes/ver_paciente/{id}/`; `ver_paciente`; `verPaciente.html`.
- Regla: propietario; edad legacy aproximada `days // 365`; muestra datos y desactivación.
- Migración: `GET /api/v1/patients/{id}/`; `PatientDetailPage`. Estado: VERIFIED; API y E2E pasan.

### FUNC-011 — Editar paciente
- URL/View/Template: `/registroPacientes/editar_paciente/{id}/`; `editar_paciente`; `editarPaciente.html`.
- Reglas: mayúsculas; teléfono único por médico; campos requeridos en HTML; permite estado A/I. PRE_EXISTING_BUG: no comprueba email duplicado antes del constraint.
- Migración: `PATCH /api/v1/patients/{id}/`; `PatientEditPage`. Estado: VERIFIED; API y edición E2E pasan.

### FUNC-012 — Desactivar paciente
- URL/View: POST `/registroPacientes/eliminar_paciente/{id}/`; `eliminar_paciente`.
- Regla: borrado lógico, `estatus='I'`; no borra relaciones. Migración: `POST /api/v1/patients/{id}/deactivate/`. Estado: VERIFIED; confirmación y efecto E2E pasan.

### FUNC-013 — Selector/autocompletado de pacientes
- URLs/Views/Templates: `/menu_historial/?paciente_id=` + `/buscar_pacientes_ajax/?term=`; `menu_historial`, `buscar_pacientes_ajax`; historial/contactar.
- Regla: autocomplete sólo por nombre, máximo 10, propios; selección habilita módulos clínicos.
- Migración: `GET /api/v1/patients/autocomplete/?term=`; `PatientSelector`. Estado: VERIFIED; pruebas: API y flujo E2E pasan.

## Expediente clínico

### FUNC-014 — Consultar y guardar antecedentes
- URL/View/Template: GET/POST `/antecedentes/{id}/`; `antecedentes`; `antecedentes.html`; AJAX.
- Models/JS: AntescedentesMedicos; 26 radios booleanos y cuatro textos; jQuery AJAX.
- Reglas: `get_or_create` incluso al hacer GET; valores booleanos son string `True`; reasigna médico; devuelve JSON.
- Migración: `GET/PUT /api/v1/patients/{id}/medical-history/`; `MedicalHistoryPage`. Estado: VERIFIED; radios/textos y persistencia E2E pasan.

### FUNC-015 — Registrar consulta
- URL/View/Template: GET/POST `/consultas/{id}/`; `consultas`; `consultas.html`.
- Reglas: motivo a mayúsculas; diagnóstico/tratamiento/observaciones defaults y mayúsculas; fecha actual; propietario; redirige a receta.
- Migración: `POST /api/v1/patients/{id}/consultations/`; `ConsultationCreatePage`. Estado: VERIFIED; alta E2E pasa.

### FUNC-016 — Historial de consultas
- URL/View/Template: `/historial_consultas/{id}/`; `historial_consultas`; template homónimo.
- Regla: propios, descendente por fecha; acceso a receta. API: `GET /api/v1/patients/{id}/consultations/`; `ConsultationHistoryPage`. Estado: VERIFIED; historial E2E pasa.

### FUNC-017 — Receta imprimible
- URL/View/Template: `/receta/{consulta_id}/`; `receta`; `receta.html`.
- Regla: consulta propia; impresión del navegador (`window.print`). API: `GET /api/v1/consultations/{id}/`; `PrescriptionPage`. Estado: VERIFIED; receta E2E pasa.

### FUNC-018 — Menú de imágenes clínicas
- URL/View/Template: `/imagenes_clinicas/{id}/`; `imagenes_clinicas`; template homónimo. Propietario.
- Migración: `ClinicalImagesHubPage`. Estado: VERIFIED; navegación E2E pasa.

### FUNC-019 — Cargar imagen clínica
- URL/View/Template: GET/POST multipart `/cargar_imagen/{id}/`; `cargar_imagen`; `cargarImagen.html`.
- Reglas: imagen/tipo/descripción/consulta obligatorios; tipo y descripción en mayúsculas; consulta debe ser propia y del paciente; guarda por storage.
- API/React: `POST /api/v1/patients/{id}/clinical-images/`; `ClinicalImageUploadPage`. Estado: VERIFIED; multipart E2E pasa.

### FUNC-020 — Buscar imágenes clínicas
- URL/View/Template: `/buscar_imagen/{id}/?fecha=&consulta_id=`; `buscar_imagen`; template homónimo.
- Regla: filtro opcional por fecha/consulta, propios; muestra descarga/eliminación. API: `GET /api/v1/patients/{id}/clinical-images/`; `ClinicalImageListPage`. Estado: VERIFIED; filtro E2E pasa.

### FUNC-021 — Historial de imágenes
- URL/View/Template: `/historial_imagenes/{id}/`; `historial_imagenes`; template homónimo.
- Regla: descendente por fecha, propios. Comparte API de FUNC-020; `ClinicalImageListPage`. Estado: VERIFIED; historial E2E pasa.

### FUNC-022 — Eliminar imagen clínica
- URL/View: POST `/eliminar_imagen/{imagen_id}/`; `eliminar_imagen`.
- Regla: borrado físico del registro propio; captura excepción. El comportamiento del storage al borrar archivo requiere prueba.
- API: `DELETE /api/v1/clinical-images/{id}/`. Estado: VERIFIED; confirmación y eliminación E2E pasan.

### FUNC-023 — Odontograma
- URL/View/Template: GET `/odontograma/{id}/`, POST JSON `/odontograma/guardar/{id}/`; `odontograma`, `guardar_odontograma`; template con JS inline extenso.
- Models/reglas: Odontograma JSON; carga el más reciente, pero guarda con `get_or_create(paciente, medico)`; permanente, decidua y resumen; endpoint legacy `csrf_exempt`.
- API/React: `GET/PUT /api/v1/patients/{id}/odontogram/`; `OdontogramPage`; interacción dental portada. Estado: VERIFIED; superficie, resumen y guardado E2E pasan.

### FUNC-024 — Crear/actualizar estudio comparativo
- URLs/Views/Templates/Form: `/progreso/{id}/`, POST `/estudio/{id}/`; `progreso`, `estudio_comparativo_view`; `progreso.html`/`estudio_comparativo.html`; `EstudioComparativoForm`.
- Reglas: cinco imágenes “antes” requeridas al crear, cuatro “después” opcionales; drag/drop, previews y actualización parcial de archivos; asigna médico/paciente.
- API/React: `GET/PUT /api/v1/patients/{id}/comparative-study/`; `ComparativeStudyPage`. Estado: VERIFIED; creación multipart, previews y persistencia E2E pasan.

### FUNC-025 — Visualizar estudio comparativo
- URL/View/Template: `/estudio/{id}/visualizar/`; `visualizar_estudio`; `estudio_comparativo.html`.
- Regla: propietario; edad exacta; cuadrículas antes/después. Comparte API FUNC-024; integrada en `ComparativeStudyPage`. Estado: VERIFIED; API y render E2E pasan.

### FUNC-026 — Descargar PDF de estudio
- URL/Helper/Template: `/estudio/{id}/descargar-pdf/`; `pdf_progreso`; `formato_estudio.html`; xhtml2pdf.
- Regla: último estudio, propietario, nombre `Estudio_nombre_appat.pdf`; resuelve media/static. API: `GET /api/v1/patients/{id}/comparative-study/pdf/`. Estado: VERIFIED; contenido y descarga E2E comprobados.

### FUNC-027 — Consentimiento informado
- URL/View/Template: GET/POST `/consentimiento/{id}/`; `consentimiento_informado`; template homónimo.
- Reglas: `get_or_create`; sólo editable hasta aceptación; texto + INE requerido por UI; máximo 5 MB; jpg/jpeg/png/gif/pdf; fija fecha; redirige historial.
- API/React: `GET/POST /api/v1/patients/{id}/consent/`; `ConsentPage`. Estado: VERIFIED; validación, aceptación, archivo y bloqueo probados.

## Exportación y comunicación

### FUNC-028 — Exportar pacientes a Excel
- URL/View: `/exportar_pacientes/`; `exportar_pacientes`; Pandas/openpyxl.
- Regla: sólo propios; columnas legacy y nombre `Pacientes.xlsx`. API: `GET /api/v1/exports/patients.xlsx`. Estado: VERIFIED; workbook y descarga E2E probados.

### FUNC-029 — Exportar consultas a Excel
- URL/View: `/exportar_consultas/`; `exportar_consultas`; elimina timezone; propios. API: `GET /api/v1/exports/consultations.xlsx`. Estado: VERIFIED; workbook y descarga E2E probados.

### FUNC-030 — Exportar imágenes a Excel
- URL/View: `/exportar_imagenes/`; `exportar_imagenes`; metadata, propios. API: `GET /api/v1/exports/clinical-images.xlsx`. Estado: VERIFIED; workbook y descarga E2E probados.

### FUNC-031 — Contactar paciente por email
- URLs/Views/Templates: selector `/contactar_pacientes/`, formulario `/contacto/{id}/`, POST `/enviar_mensaje/`; `contactar_pacientes`, `contacto`, `enviar_mensaje`; templates y email HTML.
- Reglas: paciente propio; asunto/mensaje/id requeridos; destinatario siempre viene del modelo; texto + HTML; SMTP; confirma envío.
- API/React: `POST /api/v1/patients/{id}/email/`; `PatientContactPage`. Estado: VERIFIED; mensaje texto+HTML, destinatario y confirmación E2E con backend aislado probados.

## Citas

### FUNC-032 — Calendario/menú de citas
- URL/View/Template: `/menu_citas/`; `menu_citas`; `menu_citas.html`; calendario JS inline.
- Regla: todas las citas propias; navegación mensual, selección de día y detalle. API: `GET /api/v1/appointments/`; calendario mensual en `AppointmentsPage`. Estado: VERIFIED; calendario y navegación E2E pasan.

### FUNC-033 — Seleccionar paciente para nueva cita
- URL/View/Template: `/nueva_cita/`; `nueva_cita`; `nueva_cita.html`; Select2/autocomplete.
- Migración: selector integrado en `AppointmentCreatePage`, consume FUNC-013. Estado: VERIFIED; flujo E2E pasa.

### FUNC-034 — Registrar cita
- URL/View/Template: GET/POST `/registrar_cita/{patient_id}/`; `registrar_cita`; template homónimo.
- Reglas: fecha/hora requeridas y parseables; no pasado; 08:00–20:00 inclusive; defaults; estado P/C/A; paciente propio.
- API/React: `POST /api/v1/appointments/`; `AppointmentCreatePage`. Estado: VERIFIED; reglas API y flujo E2E pasan.

### FUNC-035 — Buscar y ver detalle de cita
- URLs/Views/Templates: `/buscar_cita/?buscador=`, `/detalle_cita/{id}/`; `buscar_cita`, `detalle_cita`; templates.
- Regla: busca nombre, apellido, teléfono o id; propios; detalle completo. API: `GET /api/v1/appointments/?search=`, `GET /api/v1/appointments/{id}/`; páginas Search/Detail. Estado: VERIFIED; API y detalle E2E pasan.

### FUNC-036 — Editar cita
- URL/View/Template: GET/POST `/editar_cita/{id}/`; `editar_cita`; template.
- Reglas: iguales a creación; actualiza todos los campos. PRE_EXISTING_BUG: formato inválido redirige a registrar usando id de cita como paciente.
- API/React: `PATCH /api/v1/appointments/{id}/`; `AppointmentEditPage`. Estado: VERIFIED; edición E2E pasa.

### FUNC-037 — Listar citas por estado
- URLs: `/citas_pendientes/`, `/citas_completadas/`, `/citas_canceladas/`; tres views/templates.
- Regla: propios, orden fecha/hora, filtros P/C/A. API: `GET /api/v1/appointments/?status=`; filtros en `AppointmentsPage`. Estado: VERIFIED; API y calendario/lista E2E pasan.

### FUNC-038 — Completar o cancelar cita
- URLs/Views: `/confirmar_asistencia/{id}/`, `/cancelar_cita/{id}/`; cambia a C/A y redirige.
- Riesgo: legacy muta por GET. API: `POST /api/v1/appointments/{id}/complete|cancel/`; acciones React. Estado: VERIFIED; transiciones, CSRF y pertenencia probadas.

## IA y operaciones

### FUNC-039 — Listar y filtrar diagnósticos
- URL/View/Template: `/diagnosticos/?paciente=&tipo_imagen=&fecha=&page=`; `diagnosticos`; template.
- Reglas: imágenes propias; estadísticas procesadas/pendientes/porcentaje/tipos. API: `GET /api/v1/diagnostics/`; `DiagnosticsPage`. Estado: VERIFIED; filtros, métricas y listado E2E probados.

### FUNC-040 — Analizar imagen con YOLO
- URL/View/Template: `/diagnosticos/resultados/{image_id}/`; `resultados`; `resultados.html`; `best.pt`.
- Reglas: imagen propia; copia storage a temporal; inferencia síncrona; guarda imagen marcada y detecciones sólo en respuesta; limpia temporales; OpenSeadragon.
- API/React: `POST /api/v1/clinical-images/{id}/analyze/`; `DiagnosticResultPage` con OpenSeadragon. Estado: VERIFIED; inferencia YOLO real, resultado persistido y dos visores E2E probados.

### FUNC-041 — Administración Django
- URL: `/admin/`; modelos registrados de pacientes, citas, usuarios. Staff/superuser; se conserva como herramienta backend. Estado: VERIFIED; registro de modelos y acceso probado.

### FUNC-042 — Recordatorios de citas por email
- Comando: `python manage.py enviar_recordatorios`; template `emails/recordatorio_cita.html`; SMTP.
- Regla pretendida: pendientes próximas 24 h con email; mensaje texto+HTML. PRE_EXISTING_BUG: filtra `DateField fecha` con datetimes e ignora `hora`; no hay scheduler en repo.
- Migración: `Citas.services.send_appointment_reminders` + comando conservado; sin pantalla. Estado: VERIFIED; selección/envío probados preservando BUG-004.
