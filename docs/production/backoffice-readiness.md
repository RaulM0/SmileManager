# Estado del Backoffice

La visibilidad clínica global es un cambio sensible: debe aprobarse y auditarse la asignación de `access_system_backoffice` antes de habilitarla con información real. El permiso existente no distingue acceso operativo y clínico; separar capacidades y definir acceso por clínica es BUSINESS/CLINICAL DECISION REQUIRED. La aplicación registra accesos, pero la base de datos de auditoría no es WORM.

Pendientes: validación clínica y legal de la visibilidad, evaluación de accesibilidad, pruebas de carga y planes PostgreSQL para los nuevos filtros, auditoría de consultas de archivos cuando se habiliten, observabilidad/alertas, S3 privado, TLS/proxy, backups y restore probado, gestión de secretos y remediación de historial Git. Este cambio no constituye aprobación de producción ni de cumplimiento.
