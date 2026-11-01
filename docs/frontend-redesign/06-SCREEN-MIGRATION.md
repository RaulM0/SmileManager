# Migración pantalla por pantalla

## Dependencias

1. Documentar contratos y conservar estado Git preexistente.
2. Tokens/CSS y app shell responsive sin cambiar el árbol de rutas.
3. Componentes compartidos de formularios/estado.
4. Inicio y agenda.
5. Pacientes + header Patient 360 y navegación local.
6. Expediente clínico y odontograma.
7. Imágenes, consentimiento y estudio comparativo.
8. Diagnóstico, privacidad, exportaciones, login.
9. Validación visual, teclado y regresión E2E.

## Matriz

| Grupo | Rutas | Estrategia | Estado |
|---|---|---|---|
| Shell | todas | router/protección/logout intactos; sidebar y drawer mobile con rutas vigentes | REDESIGNED; E2E shell y captura desktop/mobile |
| Inicio | `/` | agenda de hoy y próximas citas en tablas; resumen desde `dashboard/` | REDESIGNED; inspección visual desktop/mobile |
| Citas | `/appointments*` | calendario mensual desktop, agenda por fecha en móvil con vista mensual opcional; tabla/filtros/status existentes; error/retry y bloqueo de acción duplicada | REDESIGNED; E2E alta/edición/completar/cancelar y selector móvil; recorrido integral pendiente |
| Pacientes | `/patients*` | hub como lista de tareas, tabla, header Patient 360 y nav contextual | REDESIGNED; E2E alta/edición/búsqueda/contacto/desactivar |
| Clínico | `/clinical-record`, `/patients/:id/{record,medical-history,consultations*,odontogram,comparative-study,consent}` | contexto de paciente, antecedentes densos, odontograma con estados accesibles | REDESIGNED; E2E antecedentes/consulta/receta/odontograma/estudio/consentimiento |
| Imágenes | `/patients/:id/images*`, `/diagnostics*` | flujo clínico, upload, filtros, viewer y análisis | REDESIGNED; E2E upload/filtro/delete/diagnóstico; assets de toolbar del viewer locales |
| Administración | `/exports`, `/privacy`, `/login` | presentación sobria con acciones intactas | REDESIGNED; E2E login/privacidad/3 XLSX |

E2E conectado a backend es la evidencia de flujos críticos, pero no cubre cada estado degradado, permiso ni tamaño de pantalla. No marcar un grupo como completamente VERIFIED solo por el flujo feliz.

## Implementado en primera iteración

- Tailwind/PostCSS con tokens y preflight desactivado; Bootstrap CSS/JS se retiraron después de migrar los usos visuales.
- Shell responsive con navegación principal/administración, active state, Escape/dismiss drawer, skip link y logout.
- `PatientWorkspaceNav` mantiene contexto ID y enlaza secciones que ya tienen ruta.
- También recibieron cambios de presentación los formularios/detalles de citas y pacientes, consulta/receta, imágenes, comparación, consentimiento, diagnósticos, exportación, login y aviso de privacidad.
- Slice Tailwind 1, verificado: `PatientForm` y `AppointmentForm` dejaron sus clases visuales Bootstrap por componentes `clinical-form-*` compilados con Tailwind. Las mismas rutas/payloads/required/errores siguen pasando; capturas E2E desktop y mobile revisadas.
- Slice Tailwind 2, verificado: el listado/búsqueda de pacientes usa `clinical-action-*` y `workspace-data-table`; conserva query `q/page`, resultados, estados, acciones y paginación. En móvil usa scroll interno con aviso, sin overflow de página.
- Slice Tailwind 3, verificado: tabla/listado de citas, filtros, búsqueda, acciones por estado, estados de carga/error/empty y aviso móvil de calendario. E2E valida query `status/search`, estado Cancelada, que no aparezca Completar cuando no corresponde y ejecución de completar/cancelar.
- Slice Tailwind 4, verificado: búsqueda/historial de imágenes y resultados de diagnóstico migrados a lista clínica y tabla con miniaturas. Se mantienen `date`, `consultation_id`, `patient/type/date`, descargas, confirmación de borrado, filtros automáticos/manuales según la pantalla, enlace al análisis y respuesta de estado real. Capturas desktop/móvil revisadas.
- Slice de agenda móvil: `AppointmentCalendar` dejó el markup visual de Bootstrap. Desktop conserva la grilla de 42 días; móvil muestra por defecto citas agrupadas por fecha y ordenadas por hora, con acceso a la grilla mensual y sus enlaces mediante Agenda/Mes. Los estados aparecen en texto e indicador, sin alterar GET, filtros, acciones ni navegación. Capturas desktop/móvil revisadas y E2E del selector aprobada.
- Slice clínica de detalles: `AppointmentDetailPage` y `ClinicalRecordPage` usan composición del workspace sin clases Bootstrap. `ConsultationHistoryPage` presenta los mismos registros en una línea temporal clínica con fecha, motivo, diagnóstico y enlace a receta; se conservan GET, loading, error/retry y empty. Playwright verifica el motivo y enlace, no-overflow a 390/768 px; capturas 1280/390 revisadas.
- Slice clínica de formularios: antecedentes, nueva consulta y selección de expediente dejaron controles/superficies Bootstrap. Los 24 pares Sí/No siguen siendo radios nativos, con selección y foco visibles; cuatro notas y cuatro campos de consulta mantienen validaciones, mensajes y payload. E2E ejecuta guardado con error 400/reintento y navegación a receta, además de teclado y no-overflow 390/768. Capturas 1280/390 revisadas.
- Slice de formularios clínicos restantes: imagen clínica, consentimiento, correo al paciente y estudio comparativo usan controles clínicos, labels y estados coherentes sin alterar FormData, JSON, aceptación, selección de paciente ni PDF. El estudio conserva cinco imágenes antes requeridas al crear y cuatro después opcionales. Capturas 1280/390 revisadas y flujo E2E con error 400/reintento en los cuatro módulos. Una alerta prematura del estudio, causada por claves de error ya limpiadas, se corrigió comprobando mensajes activos.
- Slice de pacientes: hub, alta, edición, detalle y selector compartido usan acciones, superficie, búsqueda y feedback propios del workspace. Se mantienen seis rutas del hub, ocho campos de PatientForm, autocomplete y desactivación confirmada. E2E añade 503/reintento para detalle y edición, y 503/feedback/reintento para desactivación, además de alta/edición existentes.
- Slice odontograma: `Tooth`/`Dentition` retienen 52 piezas, cinco superficies y seis estados. Cuadrantes FDI visibles por nombre, herramienta activa con texto y muestra cromática, superficie de 24 px y scroll local indicado; resumen en definición semántica. GET/PUT, confirmación de limpiar, aviso de guardado y payload se preservan. Playwright comprobó selección, guardado, resumen, 24 px, un cuadrante por fila móvil, dos columnas de resumen y scroll de piezas; capturas 1280/390 revisadas.
- Slice visor/resultado: `DiagnosticResultPage` reemplaza grilla/tarjetas/tabla Bootstrap por dos paneles de imagen y tabla de detecciones densa. Autoanálisis, análisis manual, POST, imagen original/resultados y controles OpenSeadragon locales permanecen. GET de imagen muestra reintento si falla. E2E completo 3/3, assets de toolbar cargados y no-overflow 390/768; capturas 1280/390 revisadas con fixture de 1×1 px.
- Slice administración/acceso: login usa un layout clínico de dos columnas en desktop y una en móvil, conservando formulario, redirección, error, busy y control de contraseña. Privacidad usa una columna de lectura; receta conserva contenido y `window.print` con estilo de impresión; exportaciones conserva tres URLs XLSX y ofrece filas compactas. Capturas 1280/390 revisadas. Se corrigió la posición móvil del enlace XLSX al detectar recorte en la captura.
- Slice retirada Bootstrap: Inicio, creación/edición de citas, hub de imágenes, cargadores y captions se pasaron a primitives clínicas/Tailwind. Se quitó el import global y la dependencia `bootstrap`, se mantuvo `bootstrap-icons`. `npm run lint`, `npm test`, `npm run build` y Playwright 3/3 pasaron tras retirar el CSS; capturas móvil de Inicio, formulario de cita, login, receta y exportaciones inspeccionadas. Falta comparación visual exhaustiva de todas las rutas tras esta retirada.
- Pase del visor con radiografía incluida en el repositorio (`media/imagenes_clinicas/x-ray-dientes.png`): el E2E la sube, analiza y muestra original/resultado con detecciones reales. Los controles OpenSeadragon reciben rol, nombre español, `tabIndex` y activación con Espacio; Playwright comprobó foco y zoom con teclado. La tabla de detecciones informa el desplazamiento horizontal en móvil. Fechas visibles de agenda/detalle, imágenes y consentimiento se muestran en español sin alterar los valores API.
- Pase de estados parciales: `ClinicalImageListPage` separa fallo de carga de consultas del fallo del listado. Si solo falla el filtro de consultas, las imágenes siguen visibles con aviso y reintento específico; E2E fuerza 503, comprueba listado usable y recupera opciones. `DiagnosticResultPage` también pasó 503/reintento de GET y 503/reintento de análisis manual.
- Listados con datos previos: pacientes, agenda, diagnósticos e imágenes indican explícitamente cuando un filtro/recarga falla y se muestran resultados de la última carga, con reintento. El error de borrar una imagen se informa aparte del error al consultar el listado. Las respuestas GET fuera de orden se descartan al cambiar filtros o abandonar la pantalla, para que una búsqueda antigua no reemplace el resultado nuevo. Playwright forzó fallo y recuperación del filtro de citas, así como fallo y recuperación del borrado de imagen; la suite completa volvió a pasar 3/3.
- Contexto de registro al cambiar IDs: el contenido del `Outlet` se reinicia al cambiar `pathname`; detalle/edición de paciente y cita además ligan cada respuesta a su ID y descartan respuestas tardías. Los formularios de edición se montan de nuevo al cambiar de registro. Una prueba unitaria confirma que, al navegar desde un paciente cargado a otro expediente cuyo GET falla, no quedan nombre ni datos del primero en pantalla. Lint, build, Vitest 4/4 y Playwright 3/3 pasan.
- Pase `frontend-design`: se retiraron etiquetas de área en mayúsculas que repetían sidebar/Patient 360 en encabezados de trabajo; metadatos con ID de cita, consulta o imagen se conservaron en frase normal. Se compactó el margen del h1; capturas de Inicio, Pacientes, login y visor 390 px inspeccionadas después. Lint, build y E2E 3/3 pasan.
- Errores, reintentos, saving y prevención de doble envío mejorados donde la lógica existente lo permitió.
- APIs, payloads, rutas y query params se mantienen. E2E crítico y revisión visual del dashboard desktop/mobile ejecutados; tablet y estados de error intencionales aún pendientes.

