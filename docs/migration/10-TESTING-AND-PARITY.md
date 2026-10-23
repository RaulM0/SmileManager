# Testing y matriz de paridad

`VERIFIED` exige API/servicio, consumidor React cuando aplica, reglas/seguridad comprobadas y equivalencia con el comportamiento legacy inventariado.

| ID | Funcionalidad | Legacy | API | React | Tests | Paridad |
|---|---|---|---|---|---|---|
| FUNC-001 | Login | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-002 | Logout | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-003 | Sesión, perfil y layout | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-004 | Dashboard | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-005 | Privacidad | OK | N/A | VERIFIED | VERIFIED | VERIFIED |
| FUNC-006 | Hub de pacientes | OK | N/A | VERIFIED | VERIFIED | VERIFIED |
| FUNC-007 | Alta de paciente | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-008 | Listado de pacientes | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-009 | Búsqueda/paginación de pacientes | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-010 | Detalle de paciente | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-011 | Edición de paciente | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-012 | Desactivación de paciente | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-013 | Selector/autocomplete | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-014 | Antecedentes médicos | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-015 | Alta de consulta | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-016 | Historial de consultas | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-017 | Receta imprimible | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-018 | Hub de imágenes | OK | N/A | VERIFIED | VERIFIED | VERIFIED |
| FUNC-019 | Carga de imagen | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-020 | Búsqueda/filtros de imágenes | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-021 | Historial de imágenes | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-022 | Eliminación de imagen | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-023 | Odontograma | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-024 | Crear/actualizar estudio | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-025 | Visualizar estudio | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-026 | PDF del estudio | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-027 | Consentimiento | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-028 | Excel de pacientes | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-029 | Excel de consultas | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-030 | Excel de imágenes | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-031 | Correo al paciente | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-032 | Calendario de citas | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-033 | Selector para cita | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-034 | Alta de cita | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-035 | Búsqueda/detalle de cita | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-036 | Edición de cita | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-037 | Filtros por estado | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-038 | Completar/cancelar cita | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-039 | Listado/filtros diagnósticos | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-040 | Inferencia YOLO/resultados | OK | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| FUNC-041 | Django Admin | OK | VERIFIED | N/A | VERIFIED | VERIFIED |
| FUNC-042 | Recordatorios por correo | OK | VERIFIED | N/A | VERIFIED | VERIFIED |

## Evidencia automática final

- `manage.py test`: 39 pruebas pasan; cubren contratos, reglas, pertenencia, validaciones, efectos, exportación, correo, PDF, admin y recordatorios.
- `manage.py check`: sin problemas.
- `makemigrations --check --dry-run`: sin cambios pendientes.
- React: 2 pruebas Vitest pasan.
- ESLint: pasa.
- Build Vite de producción: pasa.
- Playwright: 2 pruebas pasan sobre servidor Django real, base y media aisladas.
- E2E clínico: login, privacidad, pacientes, edición/búsqueda/desactivación, antecedentes, consulta/receta, imágenes/carga/filtro/eliminación, odontograma, estudio/PDF, consentimiento, diagnóstico e inferencia YOLO real, tres Excel, correo, citas/calendario/edición/completar y logout.
- E2E responsive: menú móvil abre y conserva navegación a pacientes y diagnósticos.
- Docker Compose: configuración válida y PostgreSQL local saludable.

## Aislamiento E2E

`SmileManager.settings_e2e` crea `.e2e.sqlite3` y `.e2e-media`; el setup ejecuta migraciones y crea sólo el usuario de prueba. El teardown elimina ambos destinos. La suite no escribe en PostgreSQL ni en `media/` del usuario.

Las verificaciones SMTP usan el backend de memoria de Django y las de storage usan el contrato Django Storage sobre almacenamiento temporal. Credenciales y disponibilidad de servicios de un despliegue concreto son comprobaciones operativas, no funcionalidad pendiente del código.
