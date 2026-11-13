# Aislamiento PostgreSQL y RLS

El alcance actual implementa aislamiento en la aplicación: contexto autorizado,
clínica y membresía activas, médico asignado, políticas de consulta, servicios con
locks para escrituras y rutas protegidas de archivos. La API clínica global se
retiró. Las pruebas de PostgreSQL verifican aislamiento y concurrencia de estos
contratos. Esto no ofrece aislamiento frente a acceso SQL privilegiado.

**RLS no está implementado.** No se presenta como condición universal para que la
aplicación sea multitenant ni como garantía ya incluida. El rol SQL de la aplicación
no debe compartirse con usuarios finales ni ofrecer consultas SQL arbitrarias.
La auditoría del despliegue debe comprobar sus privilegios reales.

Si se amplía el alcance para exigir aislamiento también ante consultas SQL fuera
de los servicios, implementar RLS como una fase específica: políticas por tabla y
relaciones, rol de aplicación sin propiedad ni BYPASSRLS, FORCE ROW LEVEL SECURITY,
SET LOCAL dentro de transacciones, pooling, migraciones, mantenimiento y workers.
Deben existir pruebas adversariales directas, incluida reutilización de conexiones
y fallos de transacción. Las operaciones globales requieren una vía separada y
auditada; no conceder una excepción general a la aplicación.
