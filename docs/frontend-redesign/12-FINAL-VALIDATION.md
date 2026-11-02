# Validación final

## Executive Summary

Fase de arquitectura implementada: autenticación API migrada a JWT Bearer con refresh HttpOnly, caché en memoria mediante TanStack Query, servicios tipados para pacientes/citas/diagnósticos/imágenes y recursos clínicos, y acceso autenticado a archivos clínicos desde la SPA. `/sesiones/` sigue usando la sesión tradicional de Django. `api.tests` 42/42, lint, typecheck, Vitest 8/8, build y E2E 3/3 pasan tras corregir una regresión detectada en la conservación de listas ante 503. Ver `14-QUERY-JWT-ARCHITECTURE.md`.

Actualización de fase posterior: la aplicación fuente se migró a TS/TSX con `strict: true`, se añadieron contratos de dominio y un hook de carga reutilizable, los resultados transitorios de acciones pasan a toasts globales, y tablas/calendario/odontograma/navegación clínica se ajustaron a viewport móvil sin scroll horizontal en el barrido E2E. Falta la comprobación manual integral; por ello el estado final permanece INCOMPLETE. Ver `13-MOBILE-TYPESCRIPT-TOAST.md`.

Se implementó una primera migración amplia hacia Clinical Operations Workspace: nueva navegación lateral responsive, contexto Patient 360, prioridades operativas para Inicio, organización de formularios clínicos, mejoras de estados/feedback y una capa de tokens visuales. Las rutas/API y payloads se preservaron. La fase sigue INCOMPLETE porque no se ha comprobado manualmente cada pantalla, estado degradado, rol y tamaño de viewport.

## Design System

Tailwind CSS 3.4.17 + PostCSS, prefijo `co-`, preflight desactivado y tokens de fondo/surface/typography/spacing/semantic color definidos en `tailwind.config.cjs` y `styles/app.css`. Bootstrap CSS/JS y la dependencia `bootstrap` se retiraron tras migrar el markup visual; `bootstrap-icons` permanece como iconografía.

## UX Patterns

- Operational Dashboard con datos reales de agenda y pacientes existentes.
- Navegación principal por áreas y Patient 360 contextual, solo con rutas presentes.
- Agenda mensual desktop y agenda móvil agrupada por fecha, con la vista mensual disponible mediante selector; tabla y filtros existentes. No se añadieron intervalos ni recursos que API no ofrece.
- Listados compactos, historial de consultas como línea temporal clínica, formularios por secciones, tablas, estados textuales y diagrama FDI interactivo.
- Confirmaciones destructivas preservadas; formularios extensos permanecen en sus pantallas existentes.

## Screens

Cambios de presentación: shell, Inicio, pacientes/hub/forms/detalle/contacto, clínica/consulta/receta/historial/odontograma, citas/calendar/forms/detalle, imágenes/upload/history, diagnóstico/visor, estudio comparativo, consentimiento, exportaciones, login y aviso de privacidad.

Inspección visual de Chromium: dashboard a 1440×900, 768×1024 y 390×844; Patient 360, hubs de paciente/imágenes/expediente, listado de pacientes, selector de expediente y detalle de cita en desktop/móvil; odontograma, agenda, historial/búsqueda de imágenes, diagnóstico y visor; drawer a 390×844. Forms compartidos de paciente/cita, antecedentes/nueva consulta, imagen, consentimiento, correo y estudio, listados de imágenes/diagnóstico y línea temporal se revisaron a 1280 y 390 px. La agenda muestra cuadrícula mensual desktop y lista agrupada móvil; el selector mantiene la cuadrícula móvil con scroll local. El visor carga sus 40 recursos de control desde el build local y el E2E ahora analiza la radiografía de 612×323 px del repositorio con detecciones visibles; se revisaron capturas original/analizada y zoom por teclado. Capturas bajo `frontend/test-results/` (ignoradas por Git); falta el recorrido visual manual de cada estado y combinación de datos en todas las rutas.

## Functional parity

UI-001–UI-034 documentados. Las rutas y contratos clínicos se conservaron; la autenticación de la API React cambió de cookie de sesión/CSRF a JWT Bearer, mientras `/sesiones/` permanece separado. `PatientWorkspaceNav` comparte la consulta `patients/:id/` para mostrar nombre e ID, con fallback seguro a ID ante error/denegación. El E2E del flujo clínico recorrió alta/edición/búsqueda de paciente, antecedentes, consulta/receta, upload/filtro/borrado de imagen, odontograma, estudio/PDF, consentimiento, análisis y viewer, XLSX, email, alta/edición/completar cita, desactivar paciente y logout. Comprobó que el nombre contextual se actualice tras editar y no se muestre a otra cuenta.

El flujo E2E recorrió sus acciones hasta logout; el escenario responsive verificó overflow, visibilidad del drawer, foco inicial en el primer enlace, wrap de Shift+Tab/Tab, cierre con Escape y retorno del foco al toggle. El E2E fuerza respuestas 400 de campo en ocho formularios (paciente, cita, antecedentes, consulta, contacto por correo, carga de imagen, estudio comparativo y consentimiento), verifica `aria-invalid`, asociación `aria-describedby`, alertas generales cuando aplican y reintento exitoso. Una segunda cuenta E2E comprueba lista de pacientes vacía y rechazo de acceso al expediente ajeno. El lifecycle del servidor de prueba es administrado por setup/teardown, sin dejar procesos activos.

## Responsive

Desktop: dashboard inspeccionado a 1440 px, sidebar persistente.  
Tablet: dashboard inspeccionado a 768 px, drawer cerrado estable, acción de agenda visible; sin overflow en aserción en formularios/rutas representativos.  
Mobile: dashboard a 390 px, drawer visible/cerrable; agenda por fecha y selector Agenda/Mes comprobados; sin overflow en aserción en login, paciente, cita, antecedentes, consulta, contacto, carga/estudio/consentimiento. La navegación contextual no se evaluó en todas las rutas.

## Accessibility

Skip link, landmarks, foco visible, estados activos, etiquetas del drawer, `aria-expanded`, foco inicial/wrap de teclado/cierre Escape/retorno del foco al toggle del drawer, errores de campo asociados a controles en ocho formularios, alertas de formulario, estado de envío accesible, selector de paciente en grupo vivo, toggle de contraseña etiquetado, feedback live y odontograma con nombres accesibles. Los controles OpenSeadragon tienen nombre español, rol, foco y Espacio; E2E verificó zoom. El barrido de 29 rutas comprueba nombres básicos de botones visibles. La paleta base de texto/brand supera AA en fondos comunes; faltan combinaciones de estados y lectores de pantalla en todas las pantallas/confirmaciones. No se declara certificación WCAG.

El barrido ampliado de 29 rutas también comprueba etiquetas de campos y nombres de enlaces visibles; no encontró faltantes. Contraste de texto success/warning/info/activo/inactivo calculado en sus superficies: 6.13/5.95/7.52/6.72/6.41:1. Falta comprobar lectores de pantalla reales y etiquetas de detección sobre diversas radiografías.

## Tests

- Fase móvil/TypeScript/toasts: `npm run typecheck` PASS con `strict: true`; `npm run lint` PASS sin warnings; `npm test` PASS 5/5; `npm run build` PASS. Playwright E2E 3/3 contra Django/API con barrido a 320/360/390/768/1280 px, selección de cuadrante y toast de guardado sin error obsoleto. Build y Playwright se repitieron después de mover el toast móvil al borde inferior y extraer a `useResource` la carga de nueva consulta e imagen; la posición se comprobó por bounding box y captura. Tras activar strict, un primer E2E falló por inspeccionar imágenes internas del visor sin `src`; se ajustó la aserción a recursos con URL y la siguiente suite pasó 3/3.
- `npm run lint`: PASS.
- `npm test`: PASS — 4 archivos, 4 tests; incluye respuesta de búsqueda antigua que llega después de la vigente y cambio a un expediente denegado sin mostrar datos del paciente anterior.
- `npm run build`: PASS — bundle principal JS 361.84 kB; resultado diagnóstico lazy 352.19 kB; CSS 127.79 kB tras retirar Bootstrap y las etiquetas visuales redundantes.
- Barrido E2E posterior: PASS — 29 rutas privadas con h1, sin overflow a 1280/768/390 px y sin botones visibles sin nombre básico; se simularon 503/reintento de Inicio, GET de edición de cita y PUT de odontograma, cancelación de limpieza, búsqueda vacía y retorno a ruta protegida con query tras login. La primera corrida descubrió una redirección a Inicio; `LoginPage` se corrigió y la siguiente corrida pasó 3/3.
- Playwright contra API/Django E2E: PASS — 3 pruebas; flujo clínico con ocho errores 400 de validación y reintentos, orden de teclado representativo, carga de controles OpenSeadragon, filtros/descarga/borrado de imagen, parámetros y recuperación tras 503 en diagnósticos, acción de análisis, hints de scroll móvil, búsqueda/acciones/paginación de pacientes, filtros y completar/cancelar citas, selector Agenda/Mes con `aria-pressed`, historial clínico con enlace a receta, drawer con foco/ciclo de teclado y recuperación tras un 503 en pacientes. Capturas de agenda y línea temporal desktop/mobile y forms/listados revisadas; `dist` reconstruido antes del run.
- Tras el cambio semántico del resumen del odontograma, la primera corrida completa dio 2/3 por una aserción de texto anterior (`Caries: 1`); se actualizó a `dt/dd` y la corrida completa actual pasó 3/3, incluyendo objetivo de 24 px, columnas móviles y scroll local.
- Durante E2E el backend escribió warnings de Ultralytics por permisos del perfil del usuario; no impidieron completar solicitudes de prueba.
- Pase final de listados: `npm run lint` PASS, `npm test` PASS (3/3), `npm run build` PASS y Playwright E2E PASS (3/3). El E2E simula 503 al filtrar citas con datos anteriores, verifica aviso/reintento y simula DELETE de imagen fallido antes de borrarla con éxito. Los cuatro listados descartan respuestas GET atrasadas al cambiar filtros/ruta.
- Pase de contexto por ID: `npm run lint` PASS, `npm test` PASS (4/4), `npm run build` PASS y Playwright E2E PASS (3/3). El contenido de ruta se reinicia al cambiar `pathname`; detalle/edición de paciente/cita y formularios no presentan datos del registro anterior. Una prueba unitaria comprueba el caso paciente 1 visible → paciente 2 con GET denegado.

## Build

`vite build` correcto, Tailwind incluido y sin warning de chunk >500 kB.

## Known Issues

- Producción requiere `SECRET_KEY` y ejecutar las migraciones de `token_blacklist` antes del despliegue. Los serializers conservan URL de almacenamiento por compatibilidad; se debe verificar que el servidor de medios no exponga archivos clínicos directamente fuera de las rutas API protegidas.
- La hoja Bootstrap ya se retiró; falta comparación visual y de teclado de todas las rutas y estados tras quitar el reset global. Los recorridos E2E críticos siguen pasando.
- Se forzó 503 en pacientes, Inicio, edición y filtro de citas, odontograma, diagnóstico (GET y POST manual), filtro de consultas de imágenes, borrado de imagen y desactivación; otros módulos aún requieren pruebas específicas de fallos de red/servicio además de la validación de formularios simulada.
- Instalación reportó 3 vulnerabilidades moderadas; no se ejecutó `npm audit fix` para evitar actualizaciones no relacionadas.

## Manual Verification Required

- Recorrer todas las rutas en desktop/tablet/mobile, especialmente odontograma, agenda, forms y viewer clínico.
- Revisar combinaciones de estados, orden de foco, errores asociados, lectura por pantalla y confirmaciones por teclado en los flujos restantes.
- Probar estados vacíos/parciales y errores de red restantes. El frontend no tiene gates de rol diferenciados; la API restringe expedientes por propietario y el E2E comprobó una segunda cuenta sin acceso al primer paciente.
- Completar pase manual de formularios: orden de foco y lectura por pantalla en todos los controles, ayudas/formatos, errores y estados en resoluciones y navegadores adicionales. El E2E comprueba asociación y reintento de errores en ocho formularios; no sustituye ese pase manual.
- Repetir la inspección del visor con distintas radiografías y lector de pantalla; el E2E ya usa la radiografía de 612×323 px incluida en el repositorio y comprobó enfoque, zoom con Espacio, tiles y detecciones.
- Recorrer manualmente rutas restantes en desktop/tablet/mobile y completar teclado/lector de pantalla.
- Comparar visualmente todas las rutas tras quitar Bootstrap, incluyendo estados vacíos/de error y viewport tablet.

## Functional Regressions

No se conoce ninguna regresión funcional tras corregir el retorno de login. Flujos principales del inventario, cancelación de cita y aislamiento entre dos cuentas se ejercitaron en E2E; faltan estados de error/parciales en otros módulos y cobertura manual completa de todas las rutas.

## Final Status

INCOMPLETE
