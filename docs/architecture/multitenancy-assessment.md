# Evaluación de multitenencia

> Evaluación histórica anterior a la implementación multitenant y al retiro de las interfaces HTML. Para el estado vigente, consultar [preparación multitenant](../production/multitenancy-readiness.md).

Estado: evaluación inicial y plan incremental; el sistema todavía no ofrece aislamiento por clínica. No habilitar uso multiclínica ni interpretar el encabezado de contexto como autorización hasta completar y probar todos los bloques.

## Inventario y propiedad actual

| Componente | Clasificación actual / destino | Dependencia y riesgo |
| --- | --- | --- |
| Usuario Django, credenciales, sesiones y tokens | GLOBAL / USER-SCOPED | Un usuario puede trabajar en varias clínicas; el rol no debe inferirse de `is_staff` o de un token. |
| Perfil | USER-SCOPED | `clinica_nombre` es texto, no prueba propiedad organizacional. |
| Paciente | USER-SCOPED → TENANT-SCOPED | `medico` es anulable; teléfono y correo son únicos por médico. No existe una asignación histórica verificable a clínica. |
| Cita | TENANT-SCOPED por paciente | No tiene médico ni clínica propios; la relación con paciente debe validarse. |
| Antecedentes, consulta, odontograma, imagen, estudio, consentimiento | TENANT-SCOPED por paciente, con restricción clínica por médico | También guardan `medico`; las inconsistencias deben identificarse antes del backfill. Imagen puede referir otra consulta. |
| ClinicalRevision | TENANT-SCOPED por paciente cuando existe | `patient` puede ser nulo; recurso mediante tipo e id, snapshots contienen datos clínicos. Necesita reconciliación de huérfanos. |
| AIAnalysisRun | TENANT-SCOPED | Imagen puede ser nula tras borrado; `image_reference` no establece pertenencia. Historial y claves de idempotencia requieren migración explícita. |
| AuditEvent | SYSTEM-ONLY o TENANT-SCOPED según evento | No contiene clínica; `resource_type`/`resource_id` no siempre bastan para reconstruirla. No atribuir eventos ambiguos. |
| Modelo YOLO, configuración, catálogos y salud | SHARED CONFIGURATION / SYSTEM-ONLY | No contienen por sí mismos contexto de clínica; no compartir resultados de inferencia. |
| Backoffice y permiso `access_system_backoffice` | GLOBAL | Las vistas clínicas globales se deniegan, incluidos superusuarios; falta un flujo excepcional autorizado y auditado que sea compatible con clínicas. |
| Asignación histórica, identidad de paciente entre clínicas, acceso excepcional | REQUIRES BUSINESS DECISION | No inferirla del nombre de clínica del perfil ni del médico responsable. |

## Superficies y dependencias

`api/policies.py` filtra por `paciente.medico` y, para varios registros, también por el médico de la fila; no recibe clínica. Las API, HTML heredado (`Pacientes`, `Citas`, `DiagnosticosIA`, `Home`), exportaciones y servicios invocan esa política, pero también existen accesos ORM directos. Deben revisarse creación, detalle, acciones, descargas, PDF y consultas relacionadas; cambiar solo listados no es suficiente. El administrador Django y el backoffice tienen políticas distintas. La migración debe cerrar explícitamente toda ruta que no pueda recibir contexto seguro.

Los servicios de expediente usan transacciones, bloqueo del paciente, versión y revisiones; hay que conservarlos. La IA guarda estado, hash, idempotencia y archivos; la recuperación por comando es global y necesita alcance explícito. Storage usa rutas históricas por tipo, no por clínica. Las URLs firmadas no sustituyen autorización. Los snapshots, archivos y ejecuciones que perdieron su padre requieren inventario individual.

La autenticación usa JWT y sesiones, refresh mediante cookie y controles de origen/CSRF existentes. La membresía debe verificarse en cada operación, no incluir una autorización duradera en JWT. React usa fetch y TanStack Query con claves sin clínica; un cambio de contexto requiere cancelar/ignorar respuestas previas, limpiar estado y caché y desmontar formularios. No debe activarse un selector hasta que el backend aplique el contexto a todas las superficies.

Las migraciones históricas incluyen una bifurcación 0016 y merge 0017 en Pacientes. Debe verificarse el grafo y el estado real de migraciones en cada entorno. No se han inspeccionado ni modificado datos reales. Las pruebas existentes incluyen seguridad, integridad, concurrencia PostgreSQL y E2E; su existencia no demuestra aislamiento multiclínica.

## Plan y puertas

1. A: modelos de clínica y membresía, política explícita y resolución verificada, sin cambiar el alcance clínico existente.
2. B–C: añadir pertenencia nullable al paciente y a registros que pueden sobrevivir sin padre; inventariar, asignar mediante decisión verificable, validar y solo después exigirla. Derivar clínica por paciente cuando la FK sea obligatoria y coherente; usar FK explícita para eventos y ejecuciones cuyo padre puede desaparecer. Validar relaciones cruzadas en dominio y base de datos.
3. D–G: verificar membresías en cada operación; aplicar controles a todos los servicios, HTML, admin, archivos, auditoría, IA y backoffice. Mantener separación de acceso administrativo y clínico.
4. H: selector y aislamiento del estado React únicamente después de la aplicación completa en servidor.
5. I–J: pruebas adversariales, concurrencia y RLS en PostgreSQL real, E2E sintético, ensayo de migración, operación y documentación. Sin estas evidencias el veredicto es NOT READY.

RLS no está habilitado: requiere demostrar rol de aplicación sin BYPASSRLS, propiedad y FORCE RLS, contexto transaccional, pooling, admin, migraciones y tareas. No equivale a filtrar querysets. Backfill destructivo, movimiento de archivos y restricciones NOT NULL quedan bloqueados hasta inventario, respaldo y asignación aprobada. Rollback de esquema no revierte información clínica creada o reasignada después del cambio.
