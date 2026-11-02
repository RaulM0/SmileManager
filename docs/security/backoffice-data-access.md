# Acceso global del Backoffice

`Usuarios.access_system_backoffice` autoriza también lectura global de datos clínicos en las secciones administrativas. Esta ampliación cambia el alcance del permiso anterior: revisar las asignaciones existentes antes del despliegue. No otorga escritura clínica ni acceso a los endpoints clínicos de propietario. BUSINESS DECISION REQUIRED: gobernanza, capacitación y revisión periódica de quienes reciben este acceso. LEGAL REVIEW REQUIRED para el tratamiento de información sensible.

Pacientes, citas, antecedentes, consultas, odontograma, imágenes (metadatos), estudios (metadatos), consentimientos (metadatos), revisiones y ejecuciones IA se consultan mediante API dedicada y paginada. El acceso a listas, detalle y secciones de paciente/citas genera AuditEvent con actor, acción, recurso e ID de solicitud; no contiene payload clínico. Las respuestas se marcan no-store. No se exponen archivos ni claves de storage; vista previa y descarga administrativa no están implementadas.

Las relaciones clínicas con médico distinto al propietario del paciente se excluyen, así como revisiones que no puedan asociarse a un recurso actual coherente. Esto puede ocultar historia legacy y requiere revisión de datos, no implica que no existan registros. No existe una vinculación inequívoca de todos los eventos históricos a un paciente; no se infiere a partir de identificadores ambiguos.

| Información | Clase | Acceso |
|---|---|---|
| Usuarios y estado | Administrativa | System Admin: lectura y activar/desactivar usuarios ordinarios |
| Identidad y expediente | Clínica | System Admin: lectura auditada; sin edición |
| Revisiones | Clínica | Solo lectura auditada; acceso DBA fuera de la frontera de aplicación |
| AuditEvent | Seguridad | Solo lectura; sin payload clínico |
| AIAnalysisRun | Operacional | Solo lectura; sin edición ni recuperación desde UI |

Normal: sin acceso a endpoints backoffice. System Admin: capacidades anteriores. Django Admin técnico: modelos clínicos registrados de solo lectura, incluso superuser; revisiones y runs no expuestos. DBA: acceso técnico por fuera de estas políticas y sujeto a controles organizacionales. No hay borrado ni cambios clínicos en esta API.
