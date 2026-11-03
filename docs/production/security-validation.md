# Validación de seguridad

**Actualización de cierre:** la descripción histórica del bypass de admin debajo queda reemplazada por [admin-security.md](admin-security.md): los modelos clínicos registrados ya son solo lectura y el borrado de User se deniega desde admin, incluso para superusuario. No protege acceso directo a DB/ORM ni otros mecanismos privilegiados.

Escrituras HTML de paciente ya utilizan servicios compartidos y AuditEvent; la eliminación HTML de imagen exige POST y registra el evento sin exponer excepciones internas. La revisión legacy completa y sus pruebas negativas siguen abiertas. El build excluye el laboratorio de diseño y no produjo sourcemaps. Se identificaron literales `localhost` dentro de código de librerías de navegación como base de URL de fallback, no se ha demostrado que se realicen llamadas a un servidor local. No se declara ausencia absoluta de secretos de build por un análisis superficial.

El repositorio exige `DEBUG=False`, hosts y secreto explícitos en settings de producción; rechazo de wildcard de hosts y middleware CSRF. La prueba `check --deploy` con variables sintéticas deja W005 (HSTS includeSubDomains) y W021 (preload). No activarlos sin verificar HTTPS en todos los subdominios y las consecuencias de preload: **INFRASTRUCTURE DECISION REQUIRED**.

Cookie refresh se diseña HttpOnly; sesión/CSRF son Secure con SameSite Lax en producción. JWT access permanece válido hasta expiración después del logout; no se garantiza revocación inmediata. CORS/orígenes reales, flags observados en el dominio real, proxy, cabeceras frente a tráfico externo, límites de body y edge throttling: **INFRASTRUCTURE VERIFICATION REQUIRED**. DRF throttling en cache local no equivale a defensa distribuida.

Admin: los ModelAdmin de paciente, antecedentes, consulta, imagen, odontograma, estudio, consentimiento y cita permiten operaciones directas, por lo que omiten servicios, revisiones, auditoría o reglas. **FAIL** para despliegue clínico sin mitigación y definición operativa. AuditEvent está registrado read-only en admin; una cuenta con acceso directo a DB todavía puede modificarlo. AIAnalysisRun y ClinicalRevision no aparecen registrados en admin en esta revisión; esto no evita acceso directo a DB.

Secret scanning limitado: búsqueda local de patrones AWS access key y encabezados de claves privadas no devolvió coincidencias; no es escaneo completo ni valida historial, entropía, credenciales DB, SMTP o tokens. No se declara ausencia de secretos. Compose contiene credenciales etiquetadas locales; cualquier reutilización real requiere rotación y revisión de exposición.

Git: `git ls-files` incluye `db.sqlite3` y 276 archivos en categorías de media (10 consentimientos, 110 detecciones, 39 estudios, 29 imágenes, 88 resultados). `git log --all` encontró 16 commits que afectan esas rutas. Las ramas locales/remotas existentes fueron inventariadas; no se reescribió historial ni se examinaron copias remotas. Ver [procedimiento](../security/git-sensitive-data-remediation.md).

Health: liveness no consulta dependencias, readiness comprueba DB con `SELECT 1`; la respuesta solo informa estado. Ingress, disponibilidad de DB, degradación y alertas requieren prueba en infraestructura. Los logs estructurados excluyen query string y payload en el middleware revisado; no se ha certificado todo proveedor ni todos los logs.

Reversión de `Pacientes.0023_clinical_revisions` o `DiagnosticosIA.0001_analysis_run` puede destruir historial; **DATA LOSS RISK / IRREVERSIBLE OPERATIONALLY** sin copia restaurable. Ensayar upgrade desde un esquema histórico sintético y verificar backups antes de aplicar; `makemigrations --check` no demuestra seguridad de datos existentes.
# Ampliación de visibilidad administrativa

Las nuevas lecturas globales se limitan a usuarios con permiso explícito y generan eventos de auditoría sin payload clínico. Las relaciones clínicas incoherentes quedan excluidas. La revisión de roles, pruebas dinámicas ampliadas y controles de acceso de infraestructura siguen pendientes; ver [acceso a datos](../security/backoffice-data-access.md).
