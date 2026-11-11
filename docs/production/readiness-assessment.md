# Production readiness assessment

Actualización de seguimiento: las secciones siguientes conservan evaluaciones históricas. Consultar los resultados actuales de [etapa 1](../security/etapa-1-resultados.md) y [etapa 2](../security/etapa-2-resultados.md) para límites compartidos, sesiones, MFA, privacidad e integridad documental. El estado NO-GO permanece hasta completar las verificaciones externas pendientes.

**Backoffice:** se agregó una superficie administrativa con autorización explícita, acciones de estado auditadas y lectura operativa paginada. No concede acceso clínico universal ni cambia la frontera de DBA. La presencia del panel no cierra S3, TLS, backups, distribución Git, monitoring o decisiones clínicas/legales: el dictamen permanece **NO-GO**. Ver [arquitectura](../architecture/backoffice.md) y [permisos](../security/backoffice-authorization.md).

**Cierre de aplicación, actualización:** el bypass directo de escritura clínica por Django Admin se mitigó y se probó incluso para superusuario; la lectura requiere permisos Django pero es global para quien los posea. Las dependencias se actualizaron y los escaneos locales no encontraron avisos conocidos; falta verificar CI en Linux. Sigue **NOT READY / NO-GO** por paridad legacy/E2E incompleta, almacenamiento/backup/TLS/monitoring no verificados y distribución de Git pendiente. [Admin](admin-security.md), [dependencias](dependency-security.md), [CI](ci-security.md).

Validación de cierre: 96 tests Django en SQLite temporal, 3 omitidos allí y ejecutados correctamente con PostgreSQL temporal; 26 tests frontend tras repetirlos aisladamente, typecheck y lint correctos; build correcto sin chunk del laboratorio y sin sourcemaps. Playwright: recorrido UI principal y prueba de seguridad HTTP/navegador pasaron individualmente, no se afirma suite completa conjunta exitosa ni variante E2E PostgreSQL. El primer intento conjunto falló; los resultados y límites están en [E2E](e2e-results.md). `makemigrations --check` y `git diff --check` pasan; `check --deploy` conserva W005/W021. No se usan datos clínicos ni infraestructura real.

Evaluación inicial de la copia de trabajo; no representa certificación clínica o legal. Los estados de infraestructura indican ausencia de evidencia, no un fallo demostrado.

| Área | Estado | Evidencia | Bloqueador | Acción |
|---|---|---|---|
| Django production settings | PARTIAL | `SmileManager/settings.py` exige secret y hosts; DEBUG deshabilitado | Despliegue real desconocido | Verificar variables y checks |
| Secrets | INFRASTRUCTURE VERIFICATION REQUIRED | Variables de entorno; historial no completamente investigado | Rotaciones desconocidas | Escanear sin divulgar valores y verificar gestores |
| TLS / proxy / HSTS | INFRASTRUCTURE VERIFICATION REQUIRED | Settings HTTPS; W005/W021 pendientes | Proxy y subdominios no verificados | Verificar terminación, cabeceras y decisiones HSTS |
| Cookies / CORS / CSRF | PARTIAL | Cookies seguras y middleware CSRF; configuración real no observada | Falta prueba completa en navegador | Verificar orígenes y atributos reales |
| Authentication | PARTIAL | JWT con refresh HttpOnly y rotación | Revocación de access no inmediata | Probar ciclo completo |
| Authorization | PARTIAL | Políticas de propietario en aplicación | No hay aislamiento por clínica ni roles clínicos | Validar modelo de negocio y pruebas cruzadas |
| Files / storage | INFRASTRUCTURE VERIFICATION REQUIRED | Endpoints autorizados; políticas S3 no demostradas | Privacidad real del bucket | Revisar IAM, acceso anónimo y proxy |
| PostgreSQL | INFRASTRUCTURE VERIFICATION REQUIRED | Configuración por entorno | TLS, privilegios y capacidad no verificados | Validar instalación real |
| Backups / restore | INFRASTRUCTURE VERIFICATION REQUIRED | Plan documentado; no se demostró restauración real | OPS-001 | Simulacro DB y objetos |
| Logging / audit | PARTIAL | request ID y AuditEvent; revisiones clínicas parciales | Cobertura y retención incompletas | Revisar accesos, administración y alertas |
| Monitoring / health | PARTIAL | `/health`, `/health/ready` | No hay alertas operativas demostradas | Configurar monitoring externo |
| IA | PARTIAL | AIAnalysisRun, inferencia síncrona | RUNNING puede quedar indefinido | Recuperación segura y pruebas |
| Email | INFRASTRUCTURE VERIFICATION REQUIRED | timeout SMTP configurable | Proveedor y entrega no verificados | Ensayo SMTP aislado |
| Rate limiting / uploads | PARTIAL | Límites y validadores en aplicación | Borde y almacenamiento no verificados | Probar rutas y límites del proxy |
| Dependencies | PARTIAL | Versiones actualizadas; `pip-audit` del entorno instalado y `npm audit` sin avisos conocidos en la prueba local | Escaneo y compatibilidad Linux/CI pendientes de ejecución en GitHub; lock Python sin hashes | Verificar workflow y mantener vigilancia |
| CI/CD | PARTIAL | workflow GitHub añadido | Aún no se ejecutó en GitHub ni protege ramas | Validar pipeline y protección de rama |
| Migrations | PARTIAL | Migraciones y pruebas PostgreSQL aisladas previas | Upgrade y rollback real no verificados | Ensayar desde cero y documentar riesgo |
| E2E | PARTIAL | Suite Playwright existente | Flujo aislado completo no demostrado | Revisar aislamiento y ejecutar |
| Legacy routes | PARTIAL | Rutas HTML activas | Paridad completa no demostrada | Inventariar y probar sin retirar consumidores |
| Django admin | PARTIAL | Modelos clínicos read-only; POST add/change/delete denegado incluso a superusuario | Permisos reales y DB/ORM fuera de la frontera admin no verificados | Revisar concesiones y operación |
| Incident response | PARTIAL | No hay procedimiento integral demostrado | Responsables no definidos | Documentar y asignar responsables |
| Git history | FAIL | `db.sqlite3` y media clínica siguen rastreados | Posible distribución de datos sensibles | Coordinar contención, copias e historial |
| RPO / RTO | BUSINESS DECISION REQUIRED | No hay objetivos acordados | No puede validarse recuperación contra objetivo | Decisión de negocio y ensayo |
| Clinical / legal | CLINICAL DECISION REQUIRED / LEGAL REVIEW REQUIRED | Revisión técnica no demuestra cumplimiento | Retención, consentimiento y responsabilidades | Validación externa |

Dictamen inicial: **NOT READY** para datos clínicos reales; el resultado final requiere las verificaciones y acciones descritas.

## Resultado de esta revisión

**Technical: NOT READY. Security: NOT READY. Data integrity: NOT READY. Operations: NOT READY. Clinical/legal: NO DETERMINADO POR REVISIÓN TÉCNICA.** El bypass administrativo es una brecha de control confirmada; la existencia de DB/media rastreadas y el historial crean riesgo de distribución y requieren contención coordinada. S3, proxy y restore son controles críticos no verificados, no fallos comprobados.

Pruebas: 91 backend OK en SQLite temporal (3 omitidas de PostgreSQL); 3 pruebas concurrentes PostgreSQL OK con base temporal aleatoria creada desde migraciones; otras 6 pruebas focalizadas de storage y recuperación OK tras añadir cobertura de resultado IA histórico. Frontend: 26 tests, typecheck, lint y build OK. Chromium/HTTP: una prueba sintética ampliada PASS; véase [alcance y faltantes](e2e-results.md). No se ensayó upgrade histórico ni `showmigrations` independiente, recuperación de backup, suite E2E completa o infraestructura real.

Se incorporó un comando de inspección/recuperación de RUNNING con modo seco por defecto y salvaguarda operativa; es necesaria parada confirmada de todos los workers y el comando no puede demostrarla. La política de retención y reconciliación siguen abiertas. La ruta `design-system` aparece en el bundle y en las rutas React de producción; revisar si debe estar accesible a usuarios autenticados. No se halló Dockerfile ni `.dockerignore` en el repositorio; compose solo define PostgreSQL local. Evaluar contenedor real y pipeline externo antes del despliegue.
# Ampliación de Backoffice: revisión pendiente

La asignación existente `access_system_backoffice` ahora permite lectura global de secciones clínicas. Es necesario revisar y aprobar los destinatarios antes del despliegue; ver [acceso a datos](../security/backoffice-data-access.md). La exposición de archivos clínicos desde Backoffice no está implementada. No cambian las verificaciones externas pendientes ni el dictamen NO-GO.
