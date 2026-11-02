# Auditoría del backend de SmileManager

**Actualización fase 3:** medición sintética y optimizaciones parciales en [línea base](performance/baseline.md); N+1 de consultas e imágenes corregidos, colecciones siguen sin paginar completamente y no se afirma capacidad de producción.

**Actualización fase 2:** inventario y estado de integridad en [clinical-integrity.md](architecture/clinical-integrity.md). Los hallazgos históricos se conservan como línea base; antecedentes, odontograma y citas ahora tienen salvaguardas parciales, no una garantía clínica integral.

Fecha: 2026-11-01. Alcance: copia de trabajo actual, incluidos cambios preexistentes; revisión estática de configuración, rutas, modelos, servicios y pruebas. No es un pentest ni una evaluación de infraestructura o cumplimiento. Los hallazgos de seguridad se detallan en [security-audit.md](security-audit.md), el inventario en [api-inventory.md](api-inventory.md), el plan en [backend-improvement-plan.md](backend-improvement-plan.md) y el diseño en [backend-architecture-proposal.md](backend-architecture-proposal.md). No se modificó código de aplicación. No se ejecutaron pruebas: podrían escribir en la base, almacenamiento o archivos existentes; no se midió cobertura ni rendimiento.

## Mapa real

```text
React -- Bearer JWT --> /api/v1/ -- JWTAuthentication + IsAuthenticated
    |                       --> APIView / ViewSet --> filtros por médico
    |                            --> serializers --> algunos api/services
    |                            --> ORM: Pacientes, Citas, Usuarios
    |                            --> archivos: FileResponse / S3 o disco
    |                            --> YOLO síncrono / PDF / Excel / SMTP
    +-- cookie HttpOnly refresh --> auth/session, refresh, logout
Navegador -- sesión Django --> middleware --> vistas HTML de Pacientes,
    Citas, DiagnosticosIA, Home y Sesiones --> ORM / templates / mismos recursos
Admin Django --> auth y permisos del admin --> ORM
PostgreSQL por DATABASE_URL; SQLite en pruebas e2e; disco local o S3.
```

La ruta local `/media/` en DEBUG atraviesa el middleware de sesión, pero no comprueba propiedad del archivo. El acceso S3 depende de la política del bucket, no demostrada en el repositorio. El frontend también consume URLs de archivos; no equivale a protección del almacenamiento.

## Dictamen arquitectónico independiente

**Arquitectura dominante:** monolito Django tradicional modularizado por apps, con API DRF añadida y coexistencia de vistas server-rendered. **Patrones secundarios:** capa de servicios parcial, serializadores, ORM activo, middleware de login y funciones compartidas para IA/exportación. No es Clean/hexagonal ni una capa de dominio uniforme.

**Separación:** los servicios `api/services/` centralizan partes de pacientes, citas, consultas e imágenes; la API aún contiene reglas y persistencia directa, y el código HTML reimplementa flujos (`Pacientes/views.py`, `Citas/views.py`). **Acoplamiento:** medio-alto entre `api`, modelos de otras apps, PDF y vistas tradicionales; `Citas` depende de `Pacientes`; la carga global de YOLO une importación de la API con el modelo pesado. No se ha demostrado un ciclo de imports efectivo. **Cohesión:** `Pacientes` agrupa pacientes, historias, consultas, imágenes, odontograma, estudios y consentimientos; son conceptos relacionados pero el archivo de vistas concentra demasiadas responsabilidades. `DiagnosticosIA` tiene servicio pero no tablas propias. `Usuarios.Perfil.clinica_nombre` es texto informativo, no entidad organizacional.

**Consistencia:** baja entre rutas HTML y API en validación, método HTTP, autorización y manejo de errores. Hay DTOs explícitos, consultas con `select_related` y pruebas negativas de propiedad: son bases útiles. La implementación es mantenible a pequeña escala con esfuerzo creciente; no demuestra todavía madurez profesional de producción clínica. Evolucionar el monolito es viable sin reescribirlo.

## Hallazgos de arquitectura, datos y operación

Formato: ID — severidad/prioridad/esfuerzo; evidencia; riesgo y escenario; recomendación.

**ARCH-001 — HIGH / P1 / Alto.** `Pacientes/views.py`, `api/views.py` y `api/services/`: dos superficies con lógica divergente. Una corrección en API puede dejar la ruta HTML vulnerable o inconsistente. Extraer casos de uso compartidos y políticas, migrar o retirar rutas de forma controlada y probar paridad.

**ARCH-002 — MEDIUM / P2 / Medio.** `DiagnosticosIA/services.py:8` carga YOLO al importar, y `api/views.py:25` importa el servicio. Cada proceso puede cargar un modelo grande y fallar al arrancar si faltan pesos/dependencias; inferencia bloquea el worker. Cargar de forma controlada, limitar concurrencia y medir antes de elegir cola.

**DATA-001 — HIGH / P1 / Alto.** `Pacientes/models.py` y `api/views.py:233,401`: antecedentes y odontograma se sobrescriben; consentimientos/estudios se actualizan; no se encuentra registro clínico de cambios ni versiones. Una corrección pierde su estado anterior y autor de modificación. Definir con responsables clínicos qué debe versionarse y qué puede corregirse; registrar actor, fecha y motivo, con controles de integridad. No prescribir inmutabilidad legal sin revisión.

**DATA-002 — HIGH / P1 / Medio.** `Pacientes/models.py`: cascadas desde paciente y desde usuario para diversos registros clínicos; eliminación de imagen en `api/views.py:363`. Una eliminación administrativa puede borrar registros o desvincularlos; no se demuestra limpieza coordinada de blobs. Definir retención, desactivación y borrado autorizado; probar cascadas y reconciliación de archivos.

**DATA-003 — MEDIUM / P1 / Medio.** `api/views.py:234,416,433,464` usa `get_or_create` o selección del primero sin unicidad en base de datos para historia, odontograma, estudio o consentimiento por pareja. Solicitudes simultáneas pueden crear duplicados o sobrescribir; consentimiento hace comprobación y escritura separadas. Acordar cardinalidad, limpiar duplicados, añadir constraints y transacciones/bloqueos donde corresponda; proteger efectos en storage fuera de la transacción.

**DATA-004 — MEDIUM / P2 / Medio.** `Citas/models.py`, `api/services/appointments.py`: no hay constraint de colisión ni transiciones controladas; `complete/cancel` sobrescriben estados. El PATCH usa valores por defecto para campos omitidos en `save_appointment`, pudiendo reemplazar motivo, estado u observaciones. Preservar valores en PATCH y definir reglas de agenda/transiciones con negocio; no asumir que todas las coincidencias sean inválidas.

**PERF-001 — HIGH / P1 / Medio.** `api/views.py:165,257,286,324` y `api/services/exports.py`: dashboard de próximas citas, citas, consultas e imágenes sin paginación; exportaciones materializan todos los registros con pandas. Un historial grande agota memoria o monopoliza workers. Paginar y limitar periodos; exportación limitada o asíncrona/streaming según mediciones. Pacientes y diagnósticos sí tienen paginación; `select_related` existe en varias consultas.

**PERF-002 — MEDIUM / P2 / Medio.** Búsquedas `icontains`, concatenación y filtros de fecha (`api/views.py:189,290,505`) pueden exigir scans; FK tiene índice Django habitual, pero no hay índices compuestos específicos declarados para agenda/filtros. Medir con EXPLAIN y datos representativos antes de crear índices (p. ej. propietario/fecha). No se dispone de benchmarks ni de evidencia de un N+1 concreto en API; revisar templates y perfilado antes de afirmarlo.

**OPS-001 — HIGH / P0 / Medio.** No se encontraron estrategia de backup, restauración, RPO/RTO, cifrado ni pruebas de recuperación en configuración revisada. Una pérdida de base o bucket podría ser irrecuperable. INFRASTRUCTURE VERIFICATION REQUIRED: verificar retención, aislamiento, claves y restaurar juntos base y objetos en entorno aislado.

**OPS-002 — MEDIUM / P1 / Medio.** Logging solo puntual en IA; sin configuración estructurada, métricas, correlación, health checks ni alertas observadas. Una degradación de DB o inferencia puede pasar inadvertida. Añadir logs minimizados, errores, latencia, checks con control de acceso y alertas según operación; no registrar payloads clínicos.

**API-001 — MEDIUM / P2 / Medio.** `api/urls.py` versiona `/api/v1/`, pero no se encontró OpenAPI ni handler global específico; fechas de filtro se pasan al ORM sin validación uniforme. Respuestas de error y paginación difieren; entradas inválidas podrían generar 500. Definir contrato, validar filtros, documentar esquema y normalizar errores sin detalles internos.

**TEST-001 — HIGH / P1 / Medio.** `api/tests/` contiene 47 métodos de prueba declarados: autenticación, pacientes, citas, historia, odontograma, imágenes, diagnósticos, consentimiento y exportaciones; incluye casos de propietario ajeno. No se ha medido ejecución ni cobertura. Faltan o no se han demostrado matriz completa de métodos y rutas HTML, acceso directo a storage, concurrencia real, CSRF, límites y restauración. Añadir pruebas negativas y de integración sobre PostgreSQL y storage representativo.

## Datos, escalado y operaciones

Los modelos contienen identidad y contacto, antecedentes, consultas/diagnósticos/tratamientos, odontogramas, imágenes, resultados, estudios y consentimiento/identificación. Captura y procesamiento pasan por API o HTML; transmisión TLS y cifrado en reposo son INFRASTRUCTURE VERIFICATION REQUIRED. Exportaciones XLSX y correo amplían copias; no hay política de retención demostrada. Los campos de texto no tienen límites de negocio coherentes y odontograma acepta JSON sin esquema. ImageField valida imagen mediante Pillow en API; consentimiento valida extensión y 5 MiB, sin validar contenido real. No se ha demostrado sanitización para todas las salidas ni explotación XSS, inyección SQL o path traversal.

El diseño corresponde a propietario individual, no clínica compartida: `Paciente.medico` es nullable y `Perfil.clinica_nombre` no aísla ni asocia usuarios. La autorización por médico limita colaboración y no proporciona multi-tenant. Pasar de 1 a 10/100 clínicas requiere identidad de clínica, membresías, ámbito obligatorio en toda ruta/consulta, migración de datos y pruebas cruzadas; no basta añadir un filtro. De 100 a 10.000/1.000.000 pacientes, primero preocupan listas/exportaciones sin límite, búsqueda, inferencia y storage; dimensionamiento real requiere mediciones. El aislamiento debe resolverse antes de incorporar clínicas, no después.

Dependencias exactas en `requirements.txt` (Django 5.2.8, DRF 3.16.1 y otras), sin lock con hashes ni evidencia de escaneo automatizado. Versiones fijadas no prueban seguridad ni vigencia. `pip-audit` no está instalado; no se consultó una base de CVEs ni se identifican CVEs concretos. Revisar compatibilidad y advisories actuales, generar SBOM y escaneo reproducible; no eliminar paquetes sin análisis de uso.

No se encontró infraestructura de colas, repositorios formales, tasks periódicas gestionadas, schema OpenAPI, observabilidad integral o CI en archivos inspeccionados. Sí existe `Citas/management/commands/enviar_recordatorios.py`; comprobar programación, idempotencia y operación externa. La configuración concreta de despliegue, proxies, backup, TLS, DB, permisos y políticas de S3 requiere verificación externa.
