# Estado de migración

## Resumen

- Total funcionalidades: 42
- Verified: 42
- Tested end-to-end: 40 (FUNC-041/042 no tienen UI y se verifican en backend)
- Frontend migrated: 40 (todas las funcionalidades con pantalla; admin y recordatorios son N/A)
- Backend migrated: 42 (API o conservación backend explícita según corresponda)
- Pending/partially migrated: 0
- Blocked: 0

## En progreso

- Ninguna fase funcional en progreso; migración validada.

## Completadas

- Auditoría inicial de settings, URLs, models, views, forms, templates, JavaScript inline, middleware, signals, migrations, comando, storage, email, IA, Docker e historial Git.
- Inventario estable FUNC-001…FUNC-042.
- Infraestructura DRF y React/Vite con sesión, CSRF, rutas protegidas y cliente API.
- Backend migrado y probado para FUNC-001–004 y FUNC-007–013.
- Frontend implementado para FUNC-001–004 y FUNC-006–012; falta E2E/validación visual para `VERIFIED`.
- 13 tests Django pasan; lint, test y build React pasan.
- FUNC-013–017 implementadas en API y React (selector, antecedentes, consultas y receta).
- FUNC-032–038 implementadas y probadas en API y React.
- FUNC-032–038 implementadas en React con listado/filtros, búsqueda, alta, detalle, edición y acciones.
- 22 tests Django pasan; lint, test y build React pasan.
- FUNC-018–023 implementadas en API + React: imágenes clínicas y odontograma FDI.
- 39 tests Django pasan; lint, test, build React y flujo Playwright pasan.
- FUNC-024–027 implementadas: estudio comparativo, vista, PDF y consentimiento.
- FUNC-028–031 implementadas: exportaciones Excel y correo a pacientes.
- FUNC-039–040 implementadas: listado, métricas, inferencia YOLO y visor de resultados.
- FUNC-041 se conserva en Django Admin y está cubierto por prueba de registro/permisos.
- FUNC-042 extraída a servicio reutilizable conservando el comando y cubierta por pruebas.
- React se sirve desde Django en `/app/` y sus rutas profundas funcionan.
- Calendario mensual React restaurado con navegación y citas por estado.
- Flujo E2E verificado: login → alta/detalle paciente → selección → alta/detalle cita.
- Se corrigió la renovación del token CSRF después del login, detectada por E2E.
- Suite Playwright aislada: crea base/media temporales, inicia Django y limpia al finalizar.
- Flujo clínico E2E ampliado a expediente, imágenes, odontograma, estudio/PDF, consentimiento, exportaciones, correo y diagnóstico YOLO real.
- Menú móvil verificado; se incorporó `bootstrap.bundle` y etiquetado accesible del toggler.
- Resolución del modelo YOLO independizada del directorio actual mediante `settings.BASE_DIR`.

## Pendientes

- Ningún pendiente funcional conocido.
- En cada despliegue deben validarse credenciales/servicios SMTP y S3 como operación del entorno.

## Bloqueadas

- Ninguna por ahora.

## Último trabajo realizado

Paridad de las 42 funciones verificada; 39 pruebas backend, 2 Vitest y 2 E2E (incluida inferencia YOLO real y responsive) pasan el 2026-10-23.

## Próximo trabajo

Mantener la matriz y ejecutar la suite completa ante cambios futuros.
