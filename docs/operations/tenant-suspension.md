# Estado de una clínica

Un administrador de plataforma explícito puede usar `POST /api/v1/backoffice/clinics/<uuid>/status/` con `status` igual a `ACTIVE`, `SUSPENDED` o `INACTIVE`. Las transiciones están centralizadas y auditadas; `INACTIVE` pasa primero a `ACTIVE` antes de poder suspenderse. No existe una operación ordinaria de borrado físico de clínica.

Las APIs nuevas que validan contexto rechazan clínicas no activas; los servicios de membresías y escrituras clínicas que usan el bloqueo compartido vuelven a verificar el estado dentro de la transacción. La inferencia nueva comprueba de nuevo el estado antes de publicar resultados. Las tareas de recuperación técnica tienen alcance explícito y pueden operar sobre clínicas suspendidas para mantenimiento. La cancelación de un envío externo ya iniciado no puede garantizarse.

La suspensión no equivale todavía a una garantía integral para rutas o trabajos que no hayan completado su migración. Mantener el veredicto de preparación y la lista de superficies pendientes en multitenancy-readiness.md.
