# Estado de preparación multitenant

**NOT READY.** No habilitar clínicas independientes en producción hasta cerrar y verificar las brechas siguientes. Las pruebas existentes no demuestran cobertura integral de todas las rutas ni sustituyen la validación operacional.

## Implementado

- Clínicas, membresías, roles, invitaciones, selección de contexto en la API y administración explícita de plataforma. La membresía y el estado de la clínica se comprueban en cada operación protegida.
- APIs organizacionales para pacientes, citas, antecedentes, odontograma, consultas, imágenes, consentimientos, estudios, IA, métricas y exportaciones. Las políticas clínicas también comprueban la asignación al profesional.
- Listas administrativas por clínica de membresías, invitaciones y auditoría; la auditoría global expone solamente acciones administrativas clasificadas explícitamente. El acceso clínico global del backoffice se deniega y Django Admin no está publicado.
- Nuevos archivos privados con rutas por clínica, revisiones y eventos con contexto, servicios transaccionales, idempotencia de IA por clínica, recordatorios con alcance explícito e inventario y validación de asignaciones históricas.
- El frontend ofrece selección explícita validada en servidor, cancela o descarta respuestas atrasadas y limpia la caché al cambiar de clínica. Las pantallas clínicas usan las APIs organizacionales en contexto de médico; existe un panel inicial de administración de clínica para miembros, invitaciones y actividad.
- El backoffice de plataforma incluye una pantalla para crear clínicas inactivas, cambiar su estado y gestionar la invitación del administrador inicial. Los endpoints comprueban el rol explícito de plataforma; el permiso de backoffice heredado no lo concede.
- Al navegar, el frontend vuelve a validar el contexto antes de mostrar la pantalla; si falla, descarta la caché. Un escenario Playwright con datos sintéticos comprueba cambio de clínica, intento de acceso cruzado y suspensión de membresía usando el servidor real y una base SQLite temporal. Esto no reemplaza el E2E completo ni las pruebas de concurrencia en PostgreSQL.

## Bloqueos para producción

- Falta verificar de extremo a extremo todos los contratos y flujos clínicos del frontend, completar las funciones operativas de personal y la administración de plataforma más allá del alta y estado de clínicas, y cubrir accesibilidad y cambios de clínica en navegador real.
- Las interfaces HTML heredadas se retiraron. Falta completar la auditoría de las APIs DRF de compatibilidad, servicios, comandos, relaciones y accesos directos; las protecciones actuales no prueban que no exista ninguna vía de omisión.
- Existe un comando de backfill controlado por manifiesto, pero falta aplicarlo y reconciliarlo con asignaciones verificadas en un entorno autorizado, así como establecer las restricciones definitivas. No se ha atribuido ningún paciente histórico automáticamente. La migración de contactos por clínica y médico debe validarse en staging antes de aplicarse.
- No hay RLS. Véase [tenant-rls.md](../database/tenant-rls.md) para los requisitos de implementación y validación.
- Falta ejecutar la matriz adversarial y de concurrencia completa, y E2E con dos clínicas, incluyendo archivos, revocaciones y cambios de contexto. Una ejecución correcta de pruebas parciales o de la suite actual no acredita esos escenarios ausentes.
- Falta validación en staging de configuración, migraciones, correo, almacenamiento, recuperación, respaldo y observabilidad con las credenciales y roles reales de despliegue.

Las APIs DRF de compatibilidad que usan la política compartida bloquean recursos asignados a clínicas y no muestran registros históricos a usuarios que tienen o tuvieron membresías; durante la transición pueden devolver listas vacías o 404. Las rutas que no usan esa política requieren revisión individual.
