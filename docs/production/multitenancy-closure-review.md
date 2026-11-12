# Revisión de cierre multitenant — 2026-11-08

Referencia revisada: `dev`, commit `7d29696`, incluyendo el árbol local de trabajo.

**Resultado: integración de Git completada; implementación funcional y validación
de producción todavía pendientes.** Este informe registra una revisión y pruebas;
no aplica correcciones a la aplicación ni acredita una auditoría exhaustiva.

## Evidencia ejecutada

| Comprobación                                                                     | Resultado de esta revisión                                                                                 |
| -------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| Backend, `python manage.py test --settings=SmileManager.settings_test --noinput` | 235 descubiertas: 216 correctas, 19 omitidas; sin fallos                                                   |
| Frontend, `npm test -- --reporter=dot`                                           | 50 pruebas correctas en 25 archivos                                                                        |
| Frontend, `npm run typecheck`                                                    | Correcto                                                                                                   |
| Concurrencia con `settings_postgres_test`                                        | No ejecutada: el servicio backend dejó de estar disponible; `docker compose ps -a` no muestra contenedores |
| Playwright de dos clínicas                                                       | Se inspeccionaron los escenarios existentes; no ejecutados en esta revisión                                |

La suite SQLite omite pruebas que requieren bloqueos PostgreSQL. No extrapolar
su resultado a las carreras de invitaciones, membresías, pacientes, consentimiento,
backfill o publicación de resultados IA. Los mensajes de error de análisis/correo
emitidos por escenarios negativos no produjeron fallos de la suite.

## Implementado y conservado por el merge

- Modelos de clínicas, membresías, invitaciones y administrador de plataforma.
- Resolución del contexto por `X-Clinic-ID`, membresía y clínica activas;
  autorización clínica por médico asignado.
- Rutas organizacionales de pacientes, expedientes, citas, consultas, imágenes,
  IA, consentimiento, estudios, reportes y exportaciones.
- Administración de miembros e invitaciones, auditoría por clínica y backoffice
  de plataforma separado del acceso clínico.
- Selección de clínica, invalidación de caché y descarte de respuestas atrasadas
  al cambiar de contexto en el frontend.
- Retiro de interfaces HTML legacy; continúan las APIs DRF de compatibilidad.

## Pendientes concretos

| Prioridad           | Hallazgo y evidencia                                                                                                                                                                                                                              | Criterio de cierre                                                                                                                                                                                                                                                      |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Alta                | Contacto de paciente incompleto: `frontend/src/services/patients.ts` conserva `patients/<id>/email/`; `clinicPath` lo transforma en `clinics/patients/<id>/email/`, ruta ausente en `api/urls.py`.                                                | Implementar y probar el envío con autorización por clínica/médico, auditoría y destinatario validado, o retirar explícitamente esa función del alcance y la UI.                                                                                                         |
| Alta                | El rol `STAFF` tiene `appointments.manage` en `api/tenant_context.py`, pero ninguna otra implementación Python utiliza esa capacidad. La agenda hereda el contexto `clinical.assigned` y el frontend muestra un mensaje sin funciones para STAFF. | Implementar el flujo de personal con alcance definido y pruebas negativas, o declarar que STAFF queda fuera de la primera versión y evitar ofrecerlo como operativo.                                                                                                    |
| Alta                | Las invitaciones y el alta de clínicas exigen HTTPS en `api/tenant_views.py`; `compose.yaml` configura `TENANT_INVITATION_URL` HTTP.                                                                                                              | Configurar un flujo local comprobable y verificar alta → correo → aceptación/registro → acceso a clínica. Mantener los requisitos de producción.                                                                                                                        |
| Alta                | Las APIs de compatibilidad siguen publicadas. `scoped` restringe a datos sin clínica y usuarios sin membresías, pero esto no constituye una auditoría de cada ruta, servicio, comando y acceso directo.                                           | Inventariar todas las vías, comprobar aislamiento negativo y retirar o delimitar explícitamente la compatibilidad. No confundir retiro HTML con retiro completo de legacy.                                                                                              |
| Alta                | `Paciente.clinic`, revisiones e historial IA admiten NULL durante expand/backfill. Hay herramientas de migración, pero no una fase final de contrato que cierre los caminos antiguos.                                                             | Si hay datos previos: inventariar, asignar por manifiesto y reconciliar. Si el despliegue será nuevo: documentar que no requiere backfill histórico y definir igualmente las invariantes finales para nuevos datos. No exigir clínica a eventos globales de plataforma. |
| Alta                | Falta evidencia completa de pruebas con PostgreSQL y navegador: existen pruebas de concurrencia y dos escenarios Playwright, pero no se ejecutaron aquí ni demuestran todos los recorridos.                                                       | Ejecutar toda la suite sobre PostgreSQL temporal y E2E de dos clínicas con archivos, agenda, consultas, consentimientos, IA, revocaciones, suspensión y cambio de contexto.                                                                                             |
| Antes de producción | No se verificaron staging, almacenamiento privado, correo real, restauración de respaldo ni roles reales de base de datos.                                                                                                                        | Validar y registrar resultados en el entorno de despliegue.                                                                                                                                                                                                             |

## Decisiones de alcance adicionales

- No hay RLS implementado. Es una capa adicional de aislamiento, no una condición
  universal para llamar multitenant a una aplicación. Debe quedar documentado si
  el cierre se apoya en controles de aplicación o si RLS forma parte del compromiso
  de seguridad; en ese caso faltan políticas, rol sin bypass y pruebas directas.
- El consentimiento organizacional guarda aceptación e identificación y ofrece
  lectura de `pdf_generado`, pero esa aceptación no genera el PDF. Si entregar un
  PDF de consentimiento es parte del alcance, falta implementar y probar esa
  generación; no confundirlo con el PDF del estudio comparativo.
- Hay documentación y docstrings anteriores a las rutas multitenant actuales.
  Por ejemplo `tenant_context.py` dice que el contexto no se aplica aún a rutas
  clínicas, aunque ya se aplica; el plan de datos también conserva afirmaciones
  sobre migraciones no ejecutadas en desarrollo. Actualizarlos con evidencia de
  cada entorno al cerrar, sin asumir que se migró producción.

## Orden propuesto para culminar

1. Definir el alcance de STAFF, PDF de consentimiento y compatibilidad histórica.
2. Resolver correo al paciente y el flujo de invitaciones en el entorno local.
3. Cerrar la auditoría de rutas y las invariantes de datos según el despliegue.
4. Ejecutar PostgreSQL y E2E completos, corrigiendo los fallos encontrados.
5. Validar staging y actualizar el documento de preparación con evidencia antes
   de marcar el trabajo como terminado.

El documento `multitenancy-readiness.md` continúa marcando **NOT READY**. Esta
revisión confirma motivos concretos para mantener ese estado; no identifica por
sí sola una filtración entre clínicas ni certifica ausencia de otras brechas.

## Actualización de implementación posterior a la revisión

Se implementaron contacto por clínica, agenda STAFF y su interfaz, excepción HTTP
limitada a loopback en desarrollo, PDF de consentimiento y retiro de la publicación
de las APIs clínicas globales. La compatibilidad queda limitada a regresión aislada.
Se añadió un gate de integridad de solo lectura y se migraron los E2E a las rutas
organizacionales. PostgreSQL: 248 pruebas correctas; frontend: 52 correctas, tipos
y lint válidos. El operador completó build/arranque del servidor E2E aislado.
Los diez escenarios de navegador quedaron comprobados: nueve en la última pasada
completa y el restante en una repetición dirigida después de corregir su selector
de estado (confundía el formulario con la notificación de login). El recorrido
completo de registros, archivos privados, IA, correo y recepción pasó.

El gate local detectó un paciente sin clínica asignado al usuario `smile`, y tres
revisiones sin procedencia. Tras la instrucción explícita del usuario de eliminarlo,
se eliminaron paciente, dos consultas, antecedentes, odontograma y tres revisiones
en una transacción, con registro de auditoría. El gate se repitió correctamente:
todos los contadores en cero. No se reasignaron datos. Consultar el estado actual
junto con [multitenancy-readiness.md](multitenancy-readiness.md); la tabla anterior
se conserva como evidencia de los hallazgos iniciales.
