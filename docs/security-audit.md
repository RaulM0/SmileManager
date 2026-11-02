# Auditoría de seguridad del backend

**Actualización de readiness:** Django Admin permite escritura directa de modelos clínicos y citas sin garantizar los servicios/versiones/audit: **FAIL / NO-GO** hasta mitigar y validar la operación administrativa. Git sigue rastreando DB/media; la privacidad real del bucket, TLS/proxy y la recuperación de backups no se verificaron. No se afirma cumplimiento clínico o legal. Ver [assessment](production/readiness-assessment.md), [validación](production/security-validation.md) e [inventario legacy](production/legacy-routes.md).

**Actualización fase 2:** SEC-010 continúa **PARTIALLY RESOLVED**. Las revisiones clínicas se guardan separadas de AuditEvent; citas incorporan eventos, pero faltan cobertura exhaustiva y política de retención. Ver [versionado](data/clinical-versioning.md) y [servicios](architecture/domain-services.md).

Fecha: 2026-11-01. Revisión estática de la copia de trabajo; no se probó contra despliegue, bucket ni usuarios reales. La severidad supone uso con información sensible; P0 significa bloquear producción clínica hasta mitigar o verificar. CONFIRMADO identifica comportamiento comprobado en código, no necesariamente explotación en producción. La política clínica de acceso aún no está definida. [Inventario](api-inventory.md) y [auditoría técnica](backend-audit.md).

## Actualización de implementación — fase 0

Los hallazgos históricos siguientes describen el estado anterior; esta tabla refleja el estado tras los cambios locales. Pruebas aisladas en SQLite en memoria y storage temporal; no se verificó infraestructura real.

| ID | Estado actual | Evidencia y pendiente |
|---|---|---|
| SEC-001 | RESOLVED en aplicación | Citas y logout de sesión requieren POST; análisis tradicional GET consulta y POST analiza; GET de antecedentes/consentimiento y sesión sin creación implícita. Verificar despliegue y superficies ajenas al repositorio. |
| SEC-002 | RESOLVED en aplicación | Se eliminó exención CSRF; pruebas con token, sin token y propietario ajeno. |
| SEC-003 | INFRASTRUCTURE VERIFICATION REQUIRED | `/media/` no se sirve desde Django; endpoints por sesión/JWT comprueban propiedad; serializadores y HTML dejan de entregar URLs directas. Falta comprobar bucket, CDN, proxy y accesos anónimos reales. |
| SEC-004 | PARTIALLY RESOLVED | `.gitignore` ampliado; archivos ya rastreados permanecen en índice e historial. [Procedimiento](security/git-sensitive-data-remediation.md). |
| SEC-009 | INFRASTRUCTURE VERIFICATION REQUIRED | Producción exige variables y habilita HTTPS/HSTS; proxy, TLS, dominios y headers reales aún requieren verificación. W005/W021 justificadas en [operación](operations/production-security.md). |
| SEC-014 | PARTIALLY RESOLVED | Comentario de credenciales retirado y clave de producción obligatoria; cuentas y secretos de entornos reales no verificados. |
| OPS-001 | INFRASTRUCTURE VERIFICATION REQUIRED / BUSINESS DECISION REQUIRED | [Plan de recuperación](operations/backup-recovery-plan.md); RPO/RTO y restauración real pendientes. |

No se ha comprobado que el bucket sea privado, ni se han retirado copias de Git remoto. Mantener bloqueado el uso de datos clínicos reales hasta completar esas verificaciones y las demás prioridades aplicables.

## Hallazgos

## Actualización de fase 1

SEC-005 **PARTIALLY RESOLVED**: política común de propietario; roles y clínica pendientes de negocio. SEC-006 **PARTIALLY RESOLVED**: filtros coherentes en API y rutas clínicas migradas; verificar matriz completa y datos históricos. SEC-007 **PARTIALLY RESOLVED**: límites por ámbito con cache local no distribuido; requiere controles perimetrales. SEC-008 **PARTIALLY RESOLVED**: validación central antes de almacenamiento en rutas implementadas; falta revisión de uploads administrativos y malware. SEC-010 **PARTIALLY RESOLVED**: base de eventos y correlación, sin versionado clínico ni auditoría exhaustiva. SEC-011 **RESOLVED** en exportaciones XLSX existentes; SEC-012 **RESOLVED** para `next` de login tradicional. SEC-013 **PARTIALLY RESOLVED**: rotación serializada con bloqueo DB; resta prueba concurrente PostgreSQL y revisión integral de cookie/Origin. Access emitido continúa válido hasta su expiración. Ver documentos en `docs/security/`.

Formato: ID — estado; severidad / prioridad / esfuerzo; evidencia; riesgo y escenario; recomendación.

**SEC-001 — CONFIRMADO; HIGH / P0 / Bajo.** `Citas/views.py:137-149` cambia estado con cualquier método, incluido GET; `DiagnosticosIA/views.py:49` ejecuta inferencia y persiste resultado en GET. Navegación, enlace, prefetch o solicitud externa con cookie puede modificar citas o iniciar consumo costoso. Exigir POST/CSRF en rutas de sesión, separar lectura de escritura y agregar pruebas. La explotación depende de sesión y condiciones de navegador.

**SEC-002 — CONFIRMADO; HIGH / P0 / Bajo.** `Pacientes/views.py:524` usa `@csrf_exempt` en POST que sobrescribe odontograma de usuario autenticado. Una solicitud forjada podría alterar datos clínicos cuando el navegador envía sesión; SameSite Lax mitiga algunos escenarios cross-site, no protege todos los contextos same-site ni reemplaza CSRF. Eliminar exención, exigir token y validar origen y esquema; verificar dinámicamente.

**SEC-003 — CONFIRMADO en modo local; HIGH / P0 / Medio.** `settings_local.py:25`, `SmileManager/urls.py:39` sirven `/media/` con DEBUG; el middleware exige sesión para esa ruta pero no evalúa pertenencia. Un usuario de sesión que conozca la ruta de otro archivo puede solicitarlo. URLs se devuelven en `api/serializers.py:169,203,218`. S3 usa URLs sin firma (`settings.py:112-115`): acceso público efectivo depende de política y Block Public Access; no está comprobado. Deshabilitar publicación directa con datos reales y servir mediante autorización o bucket privado; probar acceso anónimo y entre usuarios con URL conocida.

**SEC-004 — CONFIRMADO; HIGH / P0 / Medio.** `git ls-files` incluye `db.sqlite3` y archivos bajo `media/consentimientos/ine`, `media/imagenes_clinicas`, `media/estudios` y resultados. Se desconoce si son datos reales y quién accedió. Si contienen datos sensibles, la distribución de Git e historial crea copias fuera de controles de acceso clínico. Identificar contenido y alcance sin difundirlo, involucrar responsables de seguridad/privacidad, retirar de distribución y gestionar historial y copias mediante procedimiento autorizado; evaluar incidente y obligaciones con asesoría legal. No borrar o reescribir historial sin coordinación.

**SEC-005 — CONFIRMADO como control ausente; HIGH / P1 / Medio.** `settings.py` usa solo `IsAuthenticated` y no define roles funcionales; endpoints permiten al propietario exportar, borrar imágenes, escribir historia y enviar correo. Si existen recepcionistas/asistentes con usuarios propios, no hay política que limite su función; `is_staff` es del admin, no RBAC clínico. Definir matriz de permisos por función, clínica y recurso y aplicarla en servidor; evitar inventar roles y validar con negocio.

**SEC-006 — RIESGO POTENCIAL; HIGH / P1 / Alto.** Propiedad es inconsistente: `api/views.py:228` filtra paciente por médico, detalle de imágenes y consulta por médico del recurso (`:276,355`), y otras listas por médico del paciente. Si datos históricos, transferencias o escritura administrativa crean relaciones inconsistentes, el alcance puede divergir. No se demuestra un IDOR API explotable en datos normales. Unificar política y restricciones de relaciones; probar todas las operaciones con propietarios cruzados y registros inconsistentes. No existe tenant real.

**SEC-007 — CONFIRMADO; HIGH / P1 / Medio.** Sin throttling configurado en DRF ni límites de login observados; ambos logins, `api/views.py:387` y exportaciones permiten repetición. Ataques de contraseñas o solicitudes de inferencia/exportación consumen capacidad; establecer límites efectivos por cuenta/IP y recursos en borde y aplicación, más alertas. DRF throttling por sí solo no garantiza defensa frente a DoS distribuido.

**SEC-008 — CONFIRMADO como validación insuficiente; HIGH / P1 / Medio.** `api/views.py:462-477` limita identificación a 5 MiB y extensiones, pero asigna archivo sin verificar contenido; imágenes y estudios usan ImageField sin límites explícitos de tamaño/píxeles observados. Un PDF falso o imagen costosa puede almacenarse o procesarse. Aplicar límites de request, bytes, dimensiones y formato real, procesamiento aislado, tipo seguro de respuesta y análisis de malware según riesgo; no afirmar ejecución de código sin demostración.

**SEC-009 — CONFIRMADO como brecha; HIGH / P0 / Medio.** `settings.py:15` permite `ALLOWED_HOSTS=*` por defecto; no se configuran redirect HTTPS, HSTS o `SECURE_PROXY_SSL_HEADER`. Cookies de sesión/CSRF son Secure y SameSite Lax; HttpOnly de sesión depende del valor por defecto de Django. TLS/headers podrían existir en proxy, pero no constan. Exigir hosts explícitos, proxy confiable y políticas HTTPS/HSTS después de verificar infraestructura; ejecutar `check --deploy` con configuración real aislada.

**SEC-010 — CONFIRMADO como ausencia; HIGH / P1 / Alto.** No se encontró audit log de lecturas/exportaciones/cambios ni actor y versiones históricas de toda modificación clínica. Una alteración o descarga no se puede reconstruir adecuadamente. Diseñar eventos de autenticación, acceso, exportación, edición, eliminación y administración; integridad, control de acceso y retención; evitar secretos y limitar contenido clínico.

**SEC-011 — RIESGO POTENCIAL; MEDIUM / P1 / Medio.** `api/services/exports.py` construye XLSX con valores de usuario mediante pandas/openpyxl. Valores que comienzan con `=` pueden convertirse en fórmulas al abrirse en hoja de cálculo; el alcance concreto depende de campos y cliente. Probar en entorno aislado, neutralizar celdas de texto interpretables y mantener tipos explícitos.

**SEC-012 — CONFIRMADO; MEDIUM / P1 / Bajo.** `Sesiones/views.py:20` redirige a `next` sin comprobar host permitido. Un enlace de login puede enviar a destino externo después de autenticación; validar con `url_has_allowed_host_and_scheme`. No se afirma robo de credenciales sin interacción adicional.

**SEC-013 — RIESGO POTENCIAL; MEDIUM / P1 / Medio.** `api/views.py:64-80,130-159`: JWT de acceso 5 min, refresh 8 h en cookie HttpOnly/Secure según configuración, SameSite Strict, rotación y blacklist explícitas. Logout invalida refresh pero access ya emitido sigue válido hasta expirar; dos refresh simultáneos y reutilización requieren prueba. Session GET emite access desde cookie sin comprobación explícita de origen; cookie Strict y SOP mitigan escenarios, pero revisar modelo de amenazas y CSRF/origin en todos los endpoints de cookie. No existe password reset/cambio vía API en rutas revisadas. No se demuestra un bypass de autenticación.

**SEC-014 — RIESGO POTENCIAL; MEDIUM / P1 / Bajo.** `SmileManager/urls.py:26` contiene comentario de credenciales de administrador de ejemplo; se desconoce si corresponden a cuenta activa. Verificar de forma segura en entornos, retirar credenciales por defecto si existen y rotarlas si fueron usadas. La clave de desarrollo predeterminada en `settings.py` es conocida; producción base falla si no existe variable y DEBUG es falso, pero settings alternos/configuración de DEBUG deben revisarse. No se ha verificado una clave de producción filtrada.

**SEC-015 — RIESGO POTENCIAL; MEDIUM / P2 / Medio.** `Pacientes/PDF.py` resuelve recursos a partir de URLs; según xhtml2pdf y templates podrían existir llamadas de red o fallos con S3 privado. No se probó entrada controlable ni SSRF. Limitar resolución a storage autorizado y probar; no clasificar SSRF como confirmado.

## Autenticación, autorización y archivos

La API usa SimpleJWT Bearer con access de 5 minutos, refresh de 8 horas en cookie de sesión HttpOnly, `Secure` según configuración y SameSite Strict; refresh rota y agrega a blacklist, logout invalida refresh. No se observa revocación inmediata de access, MFA, límite de intentos ni flujos de contraseña propios. La app tradicional usa sesiones Django, CSRF middleware y timeout de 30 minutos; existen las excepciones señaladas. DRF no usa SessionAuthentication por defecto. No se observó CORS abierto en settings; configuración en proxy requiere comprobación. Origin de login/refresh/logout acepta ausencia de Origin; su seguridad efectiva requiere pruebas de navegador y proxy.

La API aplica filtros por médico en pacientes, citas, consultas, imágenes, odontograma, estudios, consentimiento, exportaciones y dashboard. Tests existentes prueban varios 404 para recursos ajenos; no constituyen prueba exhaustiva. No se encontró sistema de roles de negocio ni clínica/tenant. No es correcto afirmar que todas las rutas tienen BOLA, ni que el aislamiento es completo. El acceso directo local a media es una excepción comprobada a propiedad; en S3 es condicional a políticas. El Django admin tiene sus propios permisos, que deben revisarse por usuario y grupo.

Se persisten originales y resultados en storage; URLs se exponen en serializadores y HTML, a pesar de existir endpoints FileResponse protegidos. Los archivos eliminados/reemplazados no muestran una política coordinada de borrado; verificar huérfanos y respaldos. No se ha verificado cifrado de DB, archivos, backups ni TLS real. INFRASTRUCTURE VERIFICATION REQUIRED: cifrado, KMS, políticas IAM/bucket, acceso público, logs y recuperación. No emitir URLs firmadas para bucket público; primero negar acceso público y decidir caducidad y revocación.

## OWASP

Referencia: [OWASP API Security Top 10 2023](https://api-security.owasp.org/editions/2023/en/0x11-t10/) y [lista de despliegue Django](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/). Estados acotan lo observado y no certifican ausencia de fallos.

| Categoría API 2023 | Estado | Evidencia / acción |
|---|---|---|
| API1 BOLA | CONFIRMADO para media local; REQUIERE PRUEBA DINÁMICA para API y S3 | SEC-003/006; pruebas cruzadas por recurso. |
| API2 autenticación | RIESGO POTENCIAL | SEC-007/013/014. |
| API3 propiedades | RIESGO POTENCIAL | Campos sensibles y URLs; serializers restringen varias relaciones, sin matriz de propiedades por rol. |
| API4 recursos | CONFIRMADO como falta de límites | SEC-007/008 y PERF-001. |
| API5 funciones | RIESGO POTENCIAL | SEC-005: sin política de roles definida no puede concluirse que una función viole una política existente. |
| API6 flujos sensibles | RIESGO POTENCIAL | Correo, inferencia y exportaciones repetibles. |
| API7 SSRF | NO ENCONTRADO; REQUIERE PRUEBA DINÁMICA | SEC-015, sin URL de atacante demostrada. |
| API8 configuración | CONFIRMADO | SEC-001/002/003/009. |
| API9 inventario | RIESGO POTENCIAL | Superficies HTML y API coexistentes; revisar despliegues históricos. |
| API10 consumo de APIs | NO ENCONTRADO | Sin integración de API externa de negocio identificada; S3/SMTP requieren revisión de confianza y configuración. |

OWASP Top 10 web: acceso roto y configuración insegura confirmados por las condiciones anteriores; fallas criptográficas y de componentes requieren verificación; inyección, diseño inseguro, integridad de software/datos, autenticación, logging y SSRF deben probarse según alcance. No se identificó SQL injection, XSS ni deserialización insegura explotable mediante inspección; NO ENCONTRADO no equivale a prueba de ausencia.

## Controles clínicos: gap técnico, no certificación

| Control | Estado | Brecha |
|---|---|---|
| Autenticación y propiedad | CONTROL PARCIAL | JWT/sesiones y filtros; SEC-003/005/006/007. |
| Mínimo privilegio y clínica | CONTROL PARCIAL | Sin RBAC clínico ni tenant. |
| Auditoría y trazabilidad | CONTROL AUSENTE | SEC-010; timestamps no identifican actor ni cambio. |
| Cifrado | REQUIERE VERIFICACIÓN DE INFRAESTRUCTURA | TLS, DB, bucket, backups y llaves. |
| Integridad y disponibilidad | CONTROL PARCIAL | Constraints y algunos validadores; sin versiones ni recuperación demostrada. |
| Retención, eliminación, incidentes | REQUIERE REVISIÓN LEGAL/ORGANIZACIONAL | Políticas y pruebas no constan. |
| Consentimiento | CONTROL PARCIAL | Registro técnico de aceptación; validez, contenido y prueba de identidad requieren decisión externa. |

La normativa mexicana y la aplicabilidad de cualquier otra regulación requieren **LEGAL REVIEW REQUIRED** con jurisdicción, operación, contratos y datos concretos. También se requiere evaluación clínica de correcciones/retención y revisión independiente de seguridad dinámica. No se afirma cumplimiento legal.
