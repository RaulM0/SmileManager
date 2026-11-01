# Patrones UX por tarea

| Pantalla / flujo | Patrón propuesto | Motivo y límites |
|---|---|---|
| App shell | Workspace con navegación lateral agrupada y contexto superior | Mantener todas las rutas alcanzables; navegación colapsable en tablet/mobile. Sin ocultar rutas existentes. |
| Inicio | Operational dashboard: agenda de hoy primero, próximas citas y accesos a tareas | Usar solo `dashboard/` y campos existentes; conteo de pacientes se conserva sin priorizar como KPI decorativo. |
| Citas | Resource scheduler progresivo | Mantener mes actual, Hoy/anterior/siguiente, filtros query y tabla con acciones. Día/semana/profesional son `DATA_REQUIREMENT`, no simulados. |
| Pacientes | Listado master con búsqueda/paginación y detalle clínico persistente | No forzar split pane que rompa URLs; Patient 360 se forma desde rutas ya existentes. |
| Expediente | Patient 360 con header compartido y navegación local a secciones existentes | Secciones permitidas: resumen/detalle, historia, odontograma, consultas, imágenes, estudio, consentimiento. Citas/pagos/tratamientos/documentos adicionales no aparecen si no tienen ruta/datos. |
| Historia/consultas | Clinical timeline donde fechas/entidades disponibles; tabla para comparación de registros | No sintetizar fechas ni profesional inexistente. Mantener expediente/campos completos. |
| Odontograma | Interactive Clinical Diagram FDI | Mantener geometría de cuatro cuadrantes, 52 dientes en la implementación actual, 5 superficies, selector de seis estados, resumen derivado, guardar y limpiar confirmado. |
| Imágenes | Filtros compactos + tabla/galería contextual con viewer | Preservar descarga, eliminación, upload y OpenSeadragon; para imágenes la representación visual tiene valor clínico. |
| Formularios clínicos | Secciones agrupadas, labels persistentes, errores inline, acciones sticky si largo | No cambiar esquema ni reglas required. |
| Consentimiento | Documento legible + acción condicionada explícita | No ocultar términos ni quitar paso de aceptación/documento. |
| Diagnóstico | Filtros arriba, resultados densos, análisis en workspace | Mantener parámetros e IA, mostrar error/running; no afirmar diagnóstico médico como resultado automatizado sin datos existentes. |
| Exportaciones | Lista de artefactos con tipo y acción descargar | Tres enlaces y formatos actuales; no agregar jobs ficticios. |
| Dialog | Confirmaciones destructivas ya existentes | Conservar window.confirm inicialmente o reemplazar solo con dialog accesible y paridad probada. |

