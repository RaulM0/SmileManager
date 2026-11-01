# Plan de evolución priorizado

**Readiness — NO-GO:** priorizar controles administrativos de escritura clínica, contención coordinada de DB/media en Git, privacidad efectiva del bucket, restore DB+storage y validación E2E/IDOR restante. El comando de recuperación de IA es manual y exige detener previamente todos los workers; no garantiza detección automática de un proceso activo. Ver [checklist](production/go-live-checklist.md).

Cada fase necesita responsable, pruebas negativas y criterio de aceptación. Estimaciones son relativas, no plazos. Véanse IDs en [seguridad](security-audit.md) y [backend](backend-audit.md).

## Estado de fase 0

SEC-001 y SEC-002: **RESOLVED** en aplicación y pruebas aisladas. SEC-003 y SEC-009: **INFRASTRUCTURE VERIFICATION REQUIRED**; SEC-004 y SEC-014: **PARTIALLY RESOLVED**; OPS-001: **INFRASTRUCTURE VERIFICATION REQUIRED / BUSINESS DECISION REQUIRED**. Ver [estado y evidencia](security-audit.md#actualización-de-implementación--fase-0), [remediación Git](security/git-sensitive-data-remediation.md), [seguridad de producción](operations/production-security.md) y [recuperación](operations/backup-recovery-plan.md). Los elementos de la fase 0 siguientes se conservan como criterios de cierre, no como declaración de que ya se verificaron externamente.

## Fase 0 — Bloqueadores de producción clínica

1. SEC-001/002: corregir escrituras por GET y CSRF; probar navegador, sesión y solicitudes no autorizadas. Bajo esfuerzo.
2. SEC-003/004: restringir media directa, verificar bucket y distribución Git; clasificar datos y activar procedimiento de incidente si procede. Medio; no reescribir historial sin coordinación.
3. SEC-009/014 y OPS-001: validar hosts, secretos y TLS reales, verificar cuentas de ejemplo; restaurar backup aislado de DB y archivos. Medio. Producción depende de evidencia de infraestructura.

## Fase 1 — Fundación de seguridad

Implementación inicial: ver [autorización](security/authorization-model.md), [auditoría](security/audit-log.md), [uploads](security/upload-policy.md) y [límites](security/rate-limiting.md). La fase sigue parcial hasta validar rutas y permisos de administración, política de roles, concurrencia PostgreSQL y controles de infraestructura. Los pendientes de fase 0 siguen abiertos.

Definir matriz de acceso y tenancy, cubrir cada ruta, método y acceso a archivo, incluso admin y HTML (SEC-005/006). Limitar login, inferencia, correo y exportaciones, validar archivos y tamaño, endurecer `next`, sesiones y protección de cookies (SEC-007/008/012/013). Pruebas negativas A/B, clínica A/B y relaciones inconsistentes; revisión dinámica independiente. Prioridad P1.

## Fase 2 — Integridad y arquitectura

**PARTIALLY RESOLVED:** PATCH y transiciones de cita; revisiones/versiones de antecedentes y odontograma; prueba concurrente focalizada PostgreSQL. Pendientes consentimiento, IA, storage/DB, políticas de eliminación y cobertura de todos los accesos; ver [inventario](architecture/clinical-integrity.md) y [concurrencia](data/concurrency-strategy.md). Esta fase no está cerrada.

Antes de refactorizar, corregir pérdida de datos por PATCH y acordar transiciones; constraints de cardinalidad y manejo de concurrencia (DATA-003/004). Diseñar audit log y versiones con clínica/legal (SEC-010/DATA-001/002), ensayar eliminaciones y recuperación. Compartir casos de uso y políticas de la API y HTML; migrar rutas gradualmente (ARCH-001). No unir usuarios a clínicas sin plan de migración y pruebas de aislamiento.

## Fase 3 — Rendimiento y crecimiento

**Fase 3.1 parcial:** contratos paginados y calendario por rango, ejecuciones IA con huellas e idempotencia y pruebas PostgreSQL; quedan recuperación de runs interrumpidos, consistencia storage/DB, operación real, pruebas E2E y decisiones clínicas/legales. Ver [paginación](api/pagination-contracts.md), [IA](architecture/ai-analysis-lifecycle.md) y [storage](operations/storage-reconciliation.md).

**PARTIALLY RESOLVED:** benchmark sintético PostgreSQL, N+1 corregidos, dashboard limitado, límite de exportación y observabilidad inicial. Persisten paginación de agenda/consultas/imágenes, conciliación de fallos de storage y evaluación de jobs durables; ver [mediciones](performance/baseline.md), [IA](performance/ai-inference.md) y [operación](operations/observability.md).

Paginar citas/historias/imágenes y limitar dashboard/exportaciones; medir consultas y EXPLAIN antes de índices (PERF-001/002). Limitar concurrencia y medir IA; agregar job persistente/cola solo si el SLA o volumen lo justifica (ARCH-002). Ejercicios de concurrencia contra PostgreSQL y almacenamiento realista, no benchmarks inventados.

## Fase 4 — Operación continua

Instrumentar latencias, errores, DB y procesamiento IA, alertas y trazabilidad operativa minimizada (OPS-002). Establecer RPO/RTO, backups protegidos y simulacros de restauración; inventario de activos, gestión de vulnerabilidades, SBOM y dependencia con hashes. Añadir OpenAPI y contrato de errores (API-001), pipeline de pruebas y escaneo, revisión clínica/legal y respuesta a incidentes. Verificar y repetir periódicamente.

## Quick wins

- Restringir métodos y aplicar CSRF a vistas de sesión; probar comportamiento de frontend y clientes.
- Validar `next` contra hosts permitidos y configurar hosts explícitos.
- Aplicar límites proporcionales a login e inferencia y tamaño de carga en aplicación y proxy.
- Paginar colecciones sin límite con migración de contrato de clientes.
- Evitar URLs directas expuestas y verificar bloqueo público del bucket; la migración completa de storage puede requerir esfuerzo medio.

No todos los quick wins sustituyen una solución integral: por ejemplo, throttle DRF no reemplaza protección perimetral y ocultar una URL no protege un bucket público.
