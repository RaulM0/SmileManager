# Inventario de superficies HTTP

Revisión estática 2026-11-01. El prefijo de API es `/api/v1/`. Salvo auth, DRF usa JWT Bearer e `IsAuthenticated`. P = filtro por propietario/médico en la vista o queryset; no implica RBAC ni clínica. 404 suele ocultar el recurso ajeno. La validación y permisos exactos siguen sujetos a pruebas por método. Todas las operaciones enumeradas pueden involucrar PII o información clínica; ningún endpoint tiene throttling específico observado.

| Método | Ruta relativa API | Finalidad, alcance y validación/riesgo |
|---|---|---|
| GET | auth/session/ | Público, cookie refresh; devuelve sesión/access; sin cache. |
| POST | auth/login/ | Público, usuario/contraseña validados; cookie y access; sin límite de intentos. |
| POST | auth/refresh/ | Público, cookie refresh; rota/blacklist; comprobar concurrencia/origen. |
| POST | auth/logout/ | Público, cookie refresh; blacklist; access continúa hasta expiración. |
| GET | dashboard/ | P; totales y citas; lista futura sin límite. |
| GET, POST | patients/ | P; lista paginada/búsqueda y creación; serializer valida campos, servidor asigna médico. |
| GET, PUT, PATCH | patients/{id}/ | P; datos contacto/identidad; no DELETE en viewset. |
| POST | patients/{id}/deactivate/ | P; baja lógica, no elimina historial. |
| GET | patients/autocomplete/ | P; búsqueda limitada a diez. |
| GET, PUT | patients/{id}/medical-history/ | P; antecedentes; sobrescritura sin versiones. |
| GET, POST | patients/{id}/consultations/ | P; listado sin paginar y creación de consultas clínicas. |
| GET | consultations/{id}/ | Médico de consulta; sin comprobación adicional del propietario actual del paciente. |
| GET, POST | appointments/ | P por paciente; creación valida paciente y fecha/hora; lista sin paginar. |
| GET, PUT, PATCH | appointments/{id}/ | P; edición; PATCH puede resetear campos omitidos. |
| POST | appointments/{id}/complete/ y cancel/ | P; actualiza estado sin máquina de transiciones. |
| GET, POST | patients/{id}/clinical-images/ | P; imagen valida consulta del mismo médico y paciente; sin paginación ni límite de bytes explícito. |
| GET, DELETE | clinical-images/{id}/ | Médico de imagen; DELETE borra fila, sin política de archivo demostrada. |
| GET | clinical-images/{id}/file/ y result-file/ | Médico de imagen; FileResponse; storage directo puede eludir este control. |
| POST | clinical-images/{id}/analyze/ | Médico de imagen; IA síncrona sin límite ni idempotencia. |
| GET, PUT | patients/{id}/odontogram/ | P; JSON sin esquema de dominio; modifica datos existentes. |
| GET, PUT | patients/{id}/comparative-study/ | P; archivos ImageField y cinco iniciales requeridos; URLs de storage. |
| GET | patients/{id}/comparative-study/pdf/ | P; PDF y datos clínicos; comprobar resolución storage. |
| GET | patients/{id}/comparative-study/media/{field}/ | P; whitelist de campos y FileResponse. |
| GET, POST | patients/{id}/consent/ | P; GET crea fila si falta; POST valida extensión/5 MiB y fija fecha, no valida contenido real. |
| GET | patients/{id}/consent/file/ | P; identificación mediante FileResponse. |
| POST | patients/{id}/email/ | P; asunto/mensaje validados como texto; envío y contenido sin rate limit. |
| GET | exports/patients.xlsx, consultations.xlsx, clinical-images.xlsx | Médico del paciente; descarga masiva síncrona con pandas y riesgo de fórmulas. |
| GET | diagnostics/ | P; imagen/resultados; filtros y paginación. |

Router también proporciona API root y `HEAD`/`OPTIONS` según DRF. No hay esquema OpenAPI declarado. No se ha verificado disponibilidad efectiva de cada ruta mediante solicitudes dinámicas.

## Rutas HTML y administración

`SmileManager/urls.py` publica, además de API: `/admin/` (autenticación/permisos Django admin), `/home/`, `/registroPacientes/`, `/menu_citas/`, `/diagnosticos/`, `/sesiones/login/`, `/sesiones/logout/`, `/app...`; middleware exige sesión salvo prefijos exentos. `DEBUG` añade `/media/...` con sesión pero sin autorización por archivo. URL completas y nombres concretos están en `Pacientes/urls.py`, `Citas/urls.py`, `DiagnosticosIA/urls.py` y `Home/urls.py`.

| Familia HTML | Rutas/operaciones importantes | Alcance y riesgo |
|---|---|---|
| Pacientes | registrar, todos, buscar, ver, editar, eliminar, búsqueda AJAX | Filtra `medico`; eliminación POST; duplicación de reglas frente a API. |
| Historial | antecedentes, consultas, receta, historial_consultas | Propietario de paciente o médico de consulta; datos sensibles, sin historial de cambios. |
| Archivos | cargar_imagen, buscar_imagen, eliminar_imagen, historial_imagenes | Propiedad aplicada en vistas; URLs directas y validación heredada deben probarse. |
| Exportación y comunicación | exportar_pacientes, exportar_consultas, exportar_imagenes, contacto, enviar_mensaje | Filtrado por médico; volumen, fórmulas, divulgación por correo. |
| Odontograma | odontograma; odontograma/guardar/{id}/ | Filtro propietario; POST de guardado explícitamente `csrf_exempt`. |
| Estudios y consentimiento | progreso, estudio, visualizar, descargar-pdf, consentimiento | Propietario de paciente; documentos y almacenamiento; GET puede crear registros en algunos flujos. |
| Citas | nueva, registrar, buscar, editar, pendientes/completadas/canceladas, confirmar_asistencia, cancelar_cita, detalle | Filtro por médico; confirmar/cancelar modifican incluso con GET. |
| IA | diagnosticos/ y resultados/{imagen_id}/ | Por médico de paciente; GET de resultados ejecuta análisis y guarda archivo. |
| Sesiones | login/ GET/POST; logout/ | Sesiones Django; `next` sin comprobación; logout no restringe método. |

Los métodos HTML no enumerados explícitamente se determinan por cada función: varias aceptan GET para renderizado y POST para escritura; no asumir que otros métodos reciben 405 sin probar. La política homogénea debe cubrir también admin, archivos, rutas antiguas y URLs efectivamente servidas por proxy.
