# Inventario de integridad clínica — antes de fase 2

Inventario derivado de modelos, API, HTML, servicios y tests actuales, no de datos clínicos reales. Los cambios posteriores se describen en los documentos relacionados.

| Entidad | Operación / actor | Pérdida y concurrencia | Historial / constraint actual |
|---|---|---|---|
| Paciente | Propietario crea/edita; API desactiva; HTML desactiva | PATCH de paciente conserva campos; ediciones concurrentes pueden pisarse. | created/updated, FK médico nullable SET_NULL; email y teléfono únicos por médico; cascadas desde paciente a hijos. |
| Antecedentes | Propietario lee/PUT o HTML POST | overwrite sin revisión, get_or_create puede duplicar; creación y validación separadas. | JSON no; campos boolean/texto, timestamps, FK paciente y médico CASCADE; sin unicidad ni actor de edición. |
| Consulta | Propietario crea/lista; sin edición API observada | reintento puede duplicar; eliminación por cascada paciente/médico. | fecha, FK CASCADE; sin estado de cierre o historial. Decisión clínica para addendum. |
| Cita | propietario crea/edita/completa/cancela | PATCH sustituye campos omitidos por defaults; estados terminales se sobrescriben; condiciones de carrera. | FK paciente CASCADE, timestamps; sin constraint de estado o colisión. |
| Odontograma | propietario lee/PUT o HTML POST | JSON sobrescrito, dos primeras creaciones duplican y edits se pierden. | JSON + timestamps; FK paciente/médico CASCADE; sin unicidad ni revisiones. |
| Imagen clínica | propietario carga/borra/descarga | hard delete de fila; DB y storage no son atómicos, puede haber huérfanos; FK consulta opcional CASCADE. | fecha de subida, médico FK CASCADE; sin versión de archivo ni actor de borrado completo. |
| Resultado IA | propietario solicita inferencia síncrona | escritura reemplaza referencia; reintentos/concurrencia repiten inferencia y dejan objetos; detecciones no se guardan. | Solo imagen de resultado en fila de imagen; sin versión de modelo o historial. |
| Estudio comparativo | propietario crea/edita, HTML/API | archivos reemplazados y datos sobrescritos; lecturas/escrituras simultáneas, múltiples filas. | fechas creación/actualización; FK paciente/médico CASCADE, archivos nullable, sin unicidad. |
| Consentimiento/documentos | propietario acepta, ve y descarga | comprobación y guardado separados; solicitudes paralelas pueden sustituir aceptación/archivo; storage externo. | texto y fecha nullable, identificación/PDF; FK paciente/médico CASCADE; sin versión documental ni unicidad. |

Las eliminaciones desde admin o cascadas no equivalen a una política clínica de retención. **LEGAL/CLINICAL DECISION REQUIRED:** retención, correcciones de consulta, reutilización de consentimiento, preservación y acceso a revisiones. No se ha inspeccionado una base real ni se pueden presumir duplicados o ausencia de estos. **LEGACY DATA MIGRATION REQUIRED** antes de imponer unicidad sobre datos históricos sin una auditoría autorizada.

## Estado implementado

DATA-001 **PARTIALLY RESOLVED**: revisiones y control de versión para antecedentes/odontograma, sin cobertura de otros dominios ni admin directo. DATA-002 **PARTIALLY RESOLVED**: revisiones separadas sobreviven a SET_NULL; cascadas y retención clínica existentes requieren decisión. DATA-003 **PARTIALLY RESOLVED**: servicios bloquean paciente y rechazan duplicados para dos recursos; consentimiento/estudios siguen pendientes. DATA-004 **PARTIALLY RESOLVED**: PATCH de citas y estados corregidos; decisiones de agenda pendientes. SEC-010/ARCH-001 **PARTIALLY RESOLVED**. Ver [concurrencia](../data/concurrency-strategy.md), [versionado](../data/clinical-versioning.md) y [storage](../data/storage-consistency.md).

## Esquema y eliminación

Paciente.medico es SET_NULL; antecedentes, consulta, odontograma, estudio, consentimiento e imagen dependen del paciente y médico por CASCADE; cita depende del paciente por CASCADE; imagen.consulta nullable aplica CASCADE. Consentimiento.archivo_ine/pdf y campos de estudio/resultados son nullable. No existe OneToOne clínico. Revision paciente/actor usa SET_NULL. Django no elimina necesariamente el blob al eliminar la fila; el comportamiento efectivo de storage debe verificarse. Los timestamps no identifican al editor. La API de paciente desactiva en vez de DELETE; imagen permite hard delete de fila; consulta y consentimiento no exponen DELETE en API revisada; admin y cascadas pueden eliminar más. **LEGAL DECISION REQUIRED** para retención antes de cambiar CASCADE o prohibir borrados.

El odontograma acepta posiciones FDI permanentes 11–18, 21–28, 31–38, 41–48 y deciduas 51–55, 61–65, 71–75, 81–85; cinco superficies (`mesial`, `oclusal`, `distal`, `lingual`, `vestibular`) y estados `sin_registrar`, `sano`, `caries`, `restauracion`, `ausente`, `extraccion`, `protesis`. Son los valores observados en las interfaces, no un catálogo clínico universal. El resumen acepta las seis claves actuales de conteos enteros no negativos. Se rechazan claves/valores desconocidos al escribir; un registro previo incompatible queda bloqueado para edición y requiere **LEGACY DATA MIGRATION REQUIRED**. Los datos antiguos no se transforman.
