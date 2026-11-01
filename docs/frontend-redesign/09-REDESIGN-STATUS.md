# Frontend Redesign Status

## Progress

Screens total: 34 UI flows (route and component groups).  
Analyzed: 34.  
Redesigned: 34 flows received the shared visual system; the migration matrix distinguishes page composition from global styling.  
Verified: critical E2E workflow and responsive navigation pass with exit code 0; manual all-route verification remains open.  
Blocked: 0.

## Current

Fase activa: arquitectura de servicios/consultas con TanStack Query y autenticación JWT para la API React. Detalle en `14-QUERY-JWT-ARCHITECTURE.md`. La revisión manual general previa queda para el final. El estado global continúa INCOMPLETE.

Tailwind CSS 3.4.17/PostCSS compila con preflight desactivado y prefijo `co-`. Se retiraron Bootstrap CSS/JS y la dependencia `bootstrap`; `bootstrap-icons` permanece. Router, auth gates, API client, endpoints, payloads y query parameters siguen intactos. Design docs 00–12 existen y se mantienen.

## Completed

- Full route/component/API/interaction audit; UI-001–UI-034 inventory.
- Clinical tokens, workspace shell, route-aware Patient 360 navigation and task-oriented screen patterns.
- Presentation pass across dashboard, patient, clinical, appointments, images/diagnostics, exports, login and privacy screens.
- Loading/error/empty/success feedback and retry/prevent-double-submit improvements in flows where contracts permitted.
- Patient, appointment, consultation, patient-contact, clinical-image upload, comparative-study, consent and medical-history forms now associate API field errors with controls using `aria-invalid`/`aria-describedby`, preserve form-level alert feedback, and clear stale field errors when the user edits them. Save states remain readable and duplicate submits are blocked.
- Playwright end-to-end flow covers login, privacy, patient create/edit/search, medical history, consultation/prescription/history, image upload/filter/delete, odontogram save, comparative study/PDF, consent, diagnostic run/viewer, XLSX downloads, patient email, appointment create/edit/complete/cancel, patient deactivate, logout, and patient-list recovery after a forced 503.
- Chromium screenshots inspected for dashboard at 1440×900, 768×1024 and 390×844; patient detail desktop, Patient 360 mobile, odontogram desktop, calendar desktop, diagnostic viewer desktop and mobile drawer were also inspected. E2E checks no horizontal overflow at 390/768 on login, patient create/edit/search, appointment create/edit, medical history, consultation, contact, image upload, comparative study and consent; mobile drawer focus enters the first nav link, wraps Shift+Tab/Tab at both ends, and Escape closes/restores focus to its toggle.
- Calculated contrast for primary, secondary, subtle and brand text over the common canvas/surface colors; replaced low-contrast subtle text and improved disabled controls.
- Diagnostic viewer visual inspection found externally hosted OpenSeadragon toolbar images failing to load. The package control PNGs now ship locally under Vite's configured base URL; E2E checks that they load. The initial black 1×1 fixture was later replaced for upload/analysis by the repository radiograph.
- Bootstrap migration slice 1: shared patient and appointment forms moved to Tailwind component primitives (`clinical-form-*`) with the original inputs and handlers intact. Rendered screenshots at 1280 and 390 px were reviewed; visible mobile table scroll hint added to the operational dashboard.
- Bootstrap migration slice 2: patient search/list uses Tailwind primitives for search, dense table, semantic status, accessible row actions, empty/error/loading and pagination. E2E asserts the patient search result, row action name, pagination region and mobile table hint/overflow.
- Bootstrap migration slice 3: appointment list/table, filters, search, status presentation and conditional row actions use shared Tailwind primitives. The calendar markup/behavior remains legacy; its mobile horizontal scroll is now disclosed. E2E covers status/search query retention, complete/cancel API actions and no Complete action for cancelled appointments.
- Bootstrap migration slice 4: image history/search migrated to a compact clinical image list; diagnostics migrated to a result table. E2E retains reactive consultation/date filters, diagnostic query params, direct image download, confirmed delete, empty state after delete, and opening a pending analysis. Desktop/mobile captures reviewed.
- Appointment scheduler slice: monthly grid no longer uses Bootstrap presentation classes; mobile defaults to an agenda grouped by date and ordered by time, with a labeled Agenda/Mes switch preserving the 42-day grid. Month navigation, Hoy, event links, existing filters and actions remain. Desktop/mobile captures reviewed; selector and 390 px width covered by Playwright.
- Clinical detail slice: appointment detail and record hub shed Bootstrap composition classes; consultation history becomes a clinical timeline preserving every field/link and API state. Playwright validates its content/link and 390/768 px widths; desktop/mobile timeline captures reviewed.
- Clinical form slice: medical history, consultation creation and record selection now use clinical form primitives instead of Bootstrap controls/surfaces. Native yes/no radio inputs remain; keyboard selection, field errors, retries and successful submit pass E2E. All four medical note fields are asserted visible; 1280/390 captures inspected after resetting scroll position.
- Remaining clinical form slice: clinical image upload, consent, patient email and comparative study use clinical form primitives with unchanged endpoints and payloads. E2E 3/3 covers validation failures, retry, success, image/PDF and email flows. Desktop/mobile captures reviewed. Comparative study no longer displays an error when its cleared error map contains only undefined values; E2E confirms no initial alert.
- Patient slice: hub, create, edit, detail and shared selector now use workspace controls instead of Bootstrap markup. E2E 3/3 covers create/edit/deactivate and new 503 recovery for detail, edit load and deactivation; form mobile and detail desktop captures inspected. Patient status combines text and indicator.
- Odontogram slice: domain diagram keeps all 52 teeth, five surfaces and six states, while the toolbar, quadrant labels, touch targets, summary and responsive layout were redesigned. The first E2E run hit an outdated text assertion after semantic summary markup; the focused clinical E2E passed after updating it. Browser captures at 1280/390 px reviewed, including a corrected single-column mobile layout.
- Diagnostic result slice: original/analyzed viewers and detections use clinical panels/table instead of Bootstrap. OpenSeadragon and auto/manual analyze remain. GET failure has visible retry. Full E2E 3/3 passes; initial captures used the 1×1 fixture y posteriores capturas usan la radiografía del repositorio.
- Login/administración slice: layout de acceso clínico, aviso legal, receta imprimible y filas de exportación migrados; se preservan redirect, mostrar contraseña, print y tres descargas. Capturas desktop/móvil revisadas; un enlace de exportación recortado en móvil se corrigió y se inspeccionó de nuevo.
- Retirada Bootstrap: utilidades visuales restantes en Inicio, cita, hub de imágenes, captions y loaders migradas; import, dependencia y CSS puente eliminados. Lint, Vitest 2/2, build y E2E 3/3 pasan después. CSS de producción 127.65 kB. Capturas móviles de Inicio, cita, login, receta y exportación inspeccionadas con el build sin Bootstrap.
- Barrido de las 29 rutas privadas disponibles con fixture clínico a 1280/768/390 px: encabezado principal visible, sin overflow horizontal y sin botones visibles carentes de nombre básico. E2E cubre además 503/reintento de Inicio y edición de cita, 503/reintento de PUT odontograma, cancelación de limpieza, estado vacío de búsqueda y acceso protegido tras logout. Detectó que el login podía desviar la ruta solicitada hacia Inicio por un `<Navigate>` temprano; se corrigió preservando también `search` y `hash`. Lint, build y E2E 3/3 volvieron a pasar.
- Visor con radiografía de 612×323 px del repositorio: análisis con detecciones reales, render original/analizada y capturas 1280/390 inspeccionadas. El teclado descubrió que los controles OpenSeadragon tenían tooltip pero no foco; se añadieron rol, nombre, `tabIndex` y activación con Espacio. La captura móvil después de Espacio confirma zoom. La tabla de detecciones ahora indica scroll; fechas clínicas se formatean en `es-MX`. Lint, unit, build y E2E 3/3 pasan.
- Segunda cuenta E2E sin expedientes: al iniciar sesión, el listado queda vacío y la URL directa del expediente de otro profesional muestra error sin exponer su nombre. Esto verifica el alcance por propietario que aplica la API; no se encontraron roles diferenciados ni gates por rol en `frontend/src`. Capturas adicionales 1280/390 de hubs, selector clínico, detalle de paciente y detalle de cita inspeccionadas. El primer intento E2E fue un race del test al navegar antes de esperar la segunda autenticación; corregido al esperar el nombre de usuario del shell. Suite final 3/3.
- Contexto Patient 360 mejorado: la barra clínica persistente muestra ID y nombre consultado del endpoint de paciente, actualiza el nombre después de editar y conserva solo el ID si GET falla o no hay permiso. E2E valida nombre antes/después de editar y ausencia de nombre ajeno con la segunda cuenta; captura móvil revisada. Lint/build/E2E 3/3 correctos.
- Estado parcial de búsqueda de imágenes: fallo de consultas ya no desactiva ni oculta el listado; el aviso explica la situación y reintenta solo ese filtro. Playwright forzó 503 y recuperó opciones. Resultado diagnóstico ejercitó GET 503/retry y POST manual 503/retry con radiografía real. Captura del estado parcial 390 px revisada.
- Pase visual guiado por `frontend-design`: se eliminaron 25+ etiquetas superiores que repetían la navegación; IDs útiles y nombre de paciente permanecen. Inicio, Pacientes, login y visor se inspeccionaron tras el cambio. Lint/build/E2E 3/3 correctos.
- Barrido accesible adicional en 29 rutas: todos los campos, enlaces y botones visibles del contenido tienen nombre/etiqueta detectable por label, texto o ARIA. Se calcularon contrastes de texto de estados success/warning/info/activo/inactivo; todos superan 4.5:1 en sus superficies (6.13, 5.95, 7.52, 6.72 y 6.41 respectivamente). E2E 3/3.
- Listados de pacientes, citas, diagnósticos e imágenes conservan la última respuesta con aviso y reintento al fallar una nueva consulta. El error de borrado de imagen se separó de los fallos de GET. Se ignoran respuestas atrasadas cuando cambian filtros o rutas; esto evita que un GET antiguo sustituya datos más recientes. Playwright verificó 503/reintento de filtro de citas y DELETE de imagen; un test unitario invirtió el orden de dos respuestas de búsqueda de pacientes y confirmó que prevalece el filtro vigente. Lint, Vitest 3/3, build y E2E 3/3 pasan después.
- Cambio de ID clínico: `Outlet` reinicia la pantalla al cambiar ruta; detalle/edición de paciente y cita asocian GET y error al ID actual, ignoran respuestas atrasadas y remontan formularios de edición al cambiar de registro. Una prueba unitaria nueva simula paciente previo cargado, navegación a otro expediente y GET denegado: nunca muestra el nombre anterior. Vitest 4/4, lint, build y E2E 3/3 pasan.
- Capturas adicionales del listado de pacientes y del hub de expediente a 1280/390 px inspeccionadas: tabla densa con scroll local señalado en móvil, navegación Patient 360 visible y acciones del resumen clínico alineadas sin overflow. E2E 3/3 en la nueva corrida.
- Latest validation: `npm run lint`, `npm test`, `npm run build` pass; Vitest 2 files/2 tests. Playwright 3/3 passes against rebuilt `dist`, including eight simulated API validation errors with retry across patient, appointment, medical history, consultation, patient contact, image upload, comparative study and consent; image search/date/consultation filters, direct download and confirmed delete; diagnostic `patient/type/date` params, forced-503 retry and pending analysis action; viewer toolbar assets, mobile scroll hints, patient/appointment actions and status filters, keyboard order, drawer focus handling, responsive overflow and patient-list forced-503 recovery. Native date/time picker Tab behavior remains browser-dependent. Forms, patient/appointment/image/diagnostic lists and agenda captures reviewed at relevant desktop/mobile widths.

## Pending

- Profundizar contratos runtime si la API cambia y extraer lógica compartida restante con pruebas de paridad; `strict: true` y `noImplicitAny: true` ya pasan en todo `frontend/src`.
- Revisar visualmente estados adicionales y pasar teclado/lector de pantalla en móvil; el barrido automatizado cubre 320/360/390/768/1280 px y la suite E2E pasó 3/3 tras la migración de TypeScript y el ajuste de posición del toast móvil.
- Inspect remaining clinical/form screens at desktop/tablet/mobile widths; visual review so far is representative, not exhaustive.
- Manual keyboard/focus and screen-reader review across clinical forms, dialogs, odontogram and image viewer. Semantic text colors were calculated; component-specific overlays and radiograph labels still need contrast inspection.
- Exercise API error/empty/degraded states deliberately in the remaining modules.
- Probar lector de pantalla con OpenSeadragon y contraste/posición de etiquetas de detección sobre radiografías diversas; el E2E ya usa una radiografía de tamaño clínico.
- Comparar visualmente todas las rutas tras retirar Bootstrap, especialmente estados poco frecuentes y viewport tablet; el barrido automatizado solo garantiza presencia de h1, ancho y nombres básicos de botones.

## Blocked

None. Playwright works on Windows with the repository `.venv` and installed Chromium. Django/Ultralytics emits settings-file permission warnings in the user profile but the test server and analysis flow continue.

## Last completed

Diagnósticos: se comprobó un registro que apunta a `imagenes_clinicas/carie.png` ausente del almacenamiento local. La API distingue esa condición, evita ejecutar YOLO y responde sin rutas internas; el visor informa que la imagen no está disponible y ofrece ir a cargarla al expediente. El registro original no se altera. Hay que recuperar el archivo correcto desde respaldo o volver a cargarlo; no se puede reconstruir con el nombre. Cobertura de error y enlace en backend y frontend.

Arquitectura API React migrada a JWT Bearer y refresh HttpOnly, con caché TanStack Query por recurso/filtro y servicios tipados. La última respuesta válida ante fallo de filtro se recupera del caché. Lint, typecheck, Vitest 8/8, backend 42/42, build y E2E 3/3 pasan. Producción requiere `SECRET_KEY` y migraciones de `token_blacklist`. Ver `14-QUERY-JWT-ARCHITECTURE.md`.

Fase posterior: frontend fuente migrado a TS/TSX con `strict: true`, hook compartido de GET en vistas de detalle, dashboard, historial y formularios seleccionados; layout móvil sin overflow horizontal en barrido de 320/360/390/768/1280 px; toasts globales. Lint, tipos, unitarias 5/5, build y E2E 3/3 pasan tras el tipado estricto.

Inspección de listado de pacientes y hub de expediente a 1280/390 px tras protección de contexto clínico; lint, Vitest 4/4, build y E2E 3/3 sin fallos.

## Next

Completar inspección visual/teclado y estados restantes, revisar con lector de pantalla, cerrar regresión/documentación. El aislamiento entre cuentas está cubierto; no hay roles diferenciados en este frontend. El estado final sigue INCOMPLETE hasta completar esos recorridos.
