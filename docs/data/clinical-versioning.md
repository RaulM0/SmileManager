# Versionado clínico

| Recurso        | Clasificación actual / decisión                                                                                                                                    |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Antecedentes   | CURRENT STATE + HISTORY; snapshot estructurado por versión.                                                                                                        |
| Odontograma    | CURRENT STATE + HISTORY; snapshot de JSON por versión.                                                                                                             |
| Consulta       | Creación sin edición vía API observada; **CLINICAL DECISION REQUIRED** antes de imponer APPEND-ONLY o addendum.                                                    |
| Consentimiento | **LEGAL/CLINICAL DECISION REQUIRED** para versión del texto, identidad, prueba de aceptación y retención. La implementación previa no garantiza una versión legal. |
| IA             | **BUSINESS/CLINICAL DECISION REQUIRED**; solo se conserva la imagen resultado, sin hash, versión de modelo, detecciones ni ejecución histórica.                    |

`ClinicalRevision` guarda recurso, versión, paciente y actor nullable, fecha y snapshot clínico sin archivos. El estado previo de un registro existente se captura como versión 0 al primer cambio; su autor previo es desconocido y se deja null. Nuevos registros empiezan en versión 1. La unicidad `(resource_type, resource_id, version)` solo afecta la tabla nueva. Paciente/actor son SET_NULL, por lo que las revisiones sobreviven a su borrado; decisiones de conservación y acceso necesitan revisión legal. Los snapshots contienen datos clínicos y requieren los mismos controles de acceso, backup y retención que el expediente. El audit log no duplica estos snapshots.

Al borrar el actor, SET_NULL conserva la revisión pero no su identificador; definir una identidad técnica estable y sus reglas de retención requiere **LEGAL/CLINICAL DECISION REQUIRED**. El modelo no es inmutable frente a administradores de DB ni evita modificaciones directas del expediente desde admin; estas rutas deben cerrarse o integrarse con el servicio antes de garantizar historial completo.

Los datos existentes no se modifican por la migración; se les asigna versión 0. No se agregó unicidad a antecedentes/odontogramas sin inspección autorizada: **LEGACY DATA MIGRATION REQUIRED** para identificar y resolver duplicados antes de aplicar constraints sobre filas históricas. Los estados previos a esta funcionalidad solo pueden recuperarse desde backups; no se inventa historial.

Migración `0023_clinical_revisions`: campos de versión con default y tabla nueva, sin transformación de contenido ni constraint sobre filas preexistentes. Antes de desplegar: backup verificado, revisar tamaño/locks de ALTER en la versión real de PostgreSQL y probar migración en copia aislada. El rollback de esquema elimina campos y tabla de revisiones, por tanto **destruye el historial nuevo**; restaurar o exportar bajo procedimiento autorizado antes de revertir, y coordinar despliegue de clientes que requieren `version`. No se ha evaluado el volumen real.
