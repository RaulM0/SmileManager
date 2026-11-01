# Mapeo de componentes

## Fase móvil, TypeScript y feedback (estado actual)

- `src/main.tsx` envuelve la aplicación con `ToastProvider`; `useToast()` anuncia resultados transitorios de mutaciones con roles accesibles. Los errores de campo y los GET recuperables se muestran en contexto.
- `src/hooks/useResource.ts` concentra GET tipado, loading/error/retry y descarte de resultados de otra ruta. Lo utilizan Inicio, historial de consultas, detalle/edición de paciente y cita, receta, nueva consulta y carga de imagen.
- `src/types/domain.ts` define DTOs compartidos y `src/api/client.ts` expone `api<T>`, `ApiError`, `getFormErrors` y `getErrorMessage` sin alterar rutas/payloads. Todo `src` es TS/TSX con `strict: true`.
- En móvil las tablas presentan cada fila como registro etiquetado; la agenda mensual ocupa siete columnas; Patient 360 usa enlaces en grid y el odontograma muestra un cuadrante seleccionable por dentición. Se conserva cada enlace, acción y superficie dental; el barrido E2E comprueba 320/360/390/768/1280 px.
- Las referencias a `main.jsx`, Bootstrap activo y scroll horizontal de los slices históricos siguientes describen el estado de esas fases antes de esta actualización.

## Existentes que se conservan/refinan

- `AppointmentForm`, `PatientForm`: lógica de campo/validación; actualizar presentación sin alterar contratos.
- `PatientSelector`: autocomplete compartido; mantener input callback y mejorar estados/teclado.
- `ImageViewer`: conservar integración OpenSeadragon y cleanup; ajustar contenedor.
- `AppointmentCalendar`: conservar cálculo local, API de props y links; mejorar densidad y overflow.
- `Tooth`, `Dentition`: diagrama especializado; conservar selección de superficie y FDI.
- `PatientWorkspaceNav`: contexto por ID y nombre obtenido de `patients/:id/`, con fallback a ID; navegación clínica local únicamente a rutas existentes.
- `PageHeader`/listados: clases de workspace comunes aplicadas primero a Inicio, pacientes, agenda y clínica.

## Componentes base por extracción real

- `AppLayout`: shell/sidebar/mobile navigation y contexto de usuario.
- `PageHeader`: título, subtítulo contextual y acción primaria.
- `StatusLabel`: estado textual/semántico reutilizable para citas/paciente.
- `DataTable` solo si existe repetición real; no abstraer tablas clínicas heterogéneas prematuramente.
- `FormField` solo si estructura repetida reduce divergencia de labels/errors.
- estados `LoadingState`, `EmptyState`, `ErrorState` ligeros según repetición real.

## Arquitectura de datos vigente

- `services/`: contratos tipados de pacientes, citas, diagnósticos, imágenes y recursos clínicos; las páginas ya no construyen peticiones API directamente.
- `query/keys.ts`: identidad de caché por recurso, ID y filtros; `latestCachedData.ts` conserva respuesta previa con aviso en listados.
- `hooks/useResource.ts`: GET compartido para detalle/historial; `hooks/useProtectedMedia.ts`: Blob autenticado con limpieza de URL.
- `api/client.ts`: transporte Bearer, renovación única ante 401, errores y descargas autenticadas. `AuthContext` controla identidad y limpia caché.
- Los formularios conservan estado de borrador local para que refrescar un dato remoto no sobrescriba campos en edición.

## Componentes de dominio

- `PatientContextHeader`: nombre/id/contacto/estado desde paciente disponible, links existentes.
- `ClinicalRecordNavigation`: rutas existentes del expediente con activo por location.
- `AppointmentStatus`: mapear códigos P/C/A en etiqueta.
- `OdontogramStateLegend` y `ToothSurfaceButton`: interacción clínica con nombre accesible.
- `ClinicalTimeline` en historial de consultas, mapeada a fecha, motivo, diagnóstico y receta reales; no fabricar eventos.

## Puente de estilos Bootstrap → Tailwind

- `main.jsx` ya no importa `bootstrap/dist/css/bootstrap.min.css`; `bootstrap` se retiró de dependencias tras migrar las clases visuales. `bootstrap-icons` permanece como único sistema de iconos y no depende de Bootstrap CSS.
- Superficies Bootstrap activas en JSX: layout (`container`, `row`, `col-*`), controles (`btn*`, `form-control`, `form-select`, inputs/checks), feedback (`alert*`, `badge`), tablas (`table*`, `table-responsive`) y utilidades (`d-flex`, spacing, text/color, grid). `app.css` aún contiene selectores acoplados (`.btn`, `.card`, `.table`, `.form-control`, `.container-fluid`), así que retirar solo el import rompería pantallas aunque se limpien las clases JSX.
- Orden seguro: componentes compartidos `PatientForm`/`AppointmentForm` y controles → listados/tablas → formularios clínicos por grupo → detalles/visor/odontograma → login/administración; después buscar selectores globales y clases huérfanas, comparar visualmente cada ruta y solo entonces retirar Bootstrap CSS.
- No combinar la migración de CSS con cambios API/estado. Mantener Bootstrap disponible durante cada slice y comprobar rutas, validación, foco, responsive y captura antes de avanzar.
- Slice 1 implementado: ambos forms usan clases de componente compiladas con `@apply` Tailwind para superficie, grilla 12 columnas responsive, label/control/errores/alerta/botón/spinner. No quedan referencias a `.card`, `.row`, `.col-*`, `.form-control`, `.form-select`, `.btn`, `.alert`, ni spinner Bootstrap dentro de estos dos componentes; el stylesheet global permanece para el resto de pantallas.
- Slice 2 implementado: `PatientListPage` usa primitives Tailwind para búsqueda, tabla densa, status textual con indicador, acciones icon-only nombradas, error/loading/empty y paginación. El wrapper conserva desplazamiento horizontal móvil con aviso visible; se mantienen query params, API, enlaces y disabled de paginación. Bootstrap sigue importado por las otras rutas.
- Slice 3 implementado: la tabla de citas usa los mismos primitives de datos y acciones; los filtros por estado, estado activo, búsqueda, enlaces Ver/Editar y botones condicionales Completar/Cancelar conservan comportamiento. La cuadrícula mensual se conservó funcionalmente y luego recibió presentación propia; móvil ofrece agenda por fecha y acceso explícito a la grilla.
- Slice 4 implementado: el historial/búsqueda de imágenes usa una lista densa con thumbnail contextual, metadata, descarga y eliminación; el diagnóstico usa una tabla con miniatura, paciente, tipo, descripción, estado real y acción. Filtros, efecto de autoaplicar en imagen, parámetros de URL en diagnóstico, APIs, descarga y confirmación DELETE se mantienen.
- Slice 5 implementado: `AppointmentCalendar` usa estilos propios del workspace y primitives de acciones Tailwind; `AppointmentDetailPage` y `ClinicalRecordPage` dejaron la composición Bootstrap; `ConsultationHistoryPage` usa una línea temporal clínica especializada. APIs, rutas, datos, loading/error/empty y enlaces existentes se mantienen.
- Slice 6 implementado: `MedicalHistoryPage`, `ConsultationCreatePage` y `ClinicalRecordSelectPage` usan superficies, acciones y controles de formulario clínicos. Los radios Sí/No conservan inputs nativos y semántica de fieldset; se reemplazó la presentación `btn-check` por elecciones con foco visible. Campos, errores, PUT/POST y navegación permanecen.
- Slice 7 implementado: carga de imagen clínica, consentimiento, contacto por correo y estudio comparativo usan `clinical-form-*` y estados semánticos. El estudio emplea una matriz de nueve posiciones dentro de dos secciones clínicas, con previews y requisitos condicionales intactos. El selector de archivo sigue siendo un input nativo.
- Slice 8 implementado: hub, alta, edición y detalle de paciente usan el workspace y primitives clínicos; `PatientSelector` dejó `list-group`/controles Bootstrap y mantiene la API debounceada y selección por botón. El detalle añade feedback de error/reintento para GET y error/bloqueo de doble envío para desactivación.
- Slice 9 implementado: `OdontogramPage` conserva `Tooth` y `Dentition` especializados. Se reemplazaron tarjetas y botones Bootstrap por toolbar de estados, cuadrantes FDI nombrados, superficies táctiles de 24 px, scroll local y resumen semántico; GET/PUT, estados, limpieza confirmada y payload permanecen.
- Slice 10 implementado: `DiagnosticResultPage` usa paneles comparativos y tabla de detecciones propia; mantiene `ImageViewer`/OpenSeadragon, análisis automático/manual, toolbar local, coordenadas/confianza y estado de procesamiento. El GET de imagen ahora ofrece reintento visible. Bootstrap CSS aún permanece para pantallas secundarias.
- Slice 11 implementado: login, receta, privacidad y exportaciones usan superficies/acciones del workspace. Se mantienen redirect, show password, receta imprimible y tres URLs XLSX. La vista móvil de exportaciones se corrigió tras detectar el enlace desplazado a la primera columna de la grid.
- Slice 12 implementado: Inicio, alta/edición de cita y hub de imágenes dejaron utilidades Bootstrap residuales. Cargadores de rutas protegidas y lazy, encabezados/captions y utilidades restantes migraron. La hoja Bootstrap y su bloque CSS puente se retiraron; lint, unit, build y E2E 3/3 pasan con CSS 127.65 kB. Es necesario un recorrido visual/manual de todas las rutas y estados antes de declarar verificación total.

