# Mobile, TypeScript y feedback global

## Alcance solicitado

Esta fase sustituye el desplazamiento horizontal de la UI móvil por diseños que quepan en el viewport; migra `frontend/src` de JSX/JavaScript a TSX/TypeScript con comprobación de tipos; separa contratos, acceso a datos y estado de las vistas cuando evita lógica repetida; y centraliza mensajes transitorios de acciones en toasts. Se pospone la validación final general de la fase anterior hasta terminar estos cambios.

## Contratos que se conservan

- Rutas, query parameters, autenticación, CSRF, endpoints, payloads, permisos, validaciones nativas y de API.
- Acciones en tablas, odontograma, agenda, visor, formularios, uploads, downloads y confirmaciones.
- Errores de campo asociados a cada input y estados de carga/vacío en contexto. Los errores de carga con reintento conservan su acción junto al contenido; los resultados de mutaciones y mensajes generales se anuncian con toast global.

## Auditoría móvil inicial

- Tablas de pacientes, citas, diagnósticos, detecciones e Inicio fuerzan `min-width` entre 500 y 760 px y usan scroll horizontal local. En móvil se transformarán en filas de datos etiquetadas, con todas las acciones visibles.
- El calendario Mes conserva una cuadrícula de 760 px en móvil. Se adaptará al ancho y conservará enlaces a citas y cambio Agenda/Mes.
- Patient 360 usa una tira horizontal de ocho enlaces. Se reemplazará por navegación local ajustable al ancho, manteniendo contexto y acceso a todas las secciones.
- Odontograma usa filas de 5 u 8 dientes de 72 px, con scroll. En móvil se distribuirán las piezas en varias filas sin reducir sus cinco superficies interactivas.
- El barrido automatizado comprueba 320, 360, 390, 768 y 1280 px. La comprobación manual con teclado/lector de pantalla queda pendiente.

## Arquitectura objetivo

`api/` conserva transporte CSRF y expone tipos de respuesta y error; `types/` agrupa modelos del dominio y DTOs; `hooks/` contiene carga, filtros o acciones compartidas cuando existe repetición real; `components/` mantiene controles y notificaciones; `pages/` compone la tarea y conserva la lógica específica que es más clara allí. `tsc --noEmit` será gate junto a lint, Vitest, build y Playwright.

## Toasts

Un proveedor global accesible anunciará éxito/error de acciones y no bloqueará el flujo. Los errores de validación permanecen en los campos para indicar dónde corregir; además se puede anunciar un resumen por toast. Errores persistentes con reintento y estados parciales siguen visibles en la sección porque el usuario necesita recuperar la operación.

## Estado

- Auditoría inicial: realizada.
- Responsive: tablas con celdas etiquetadas, calendario mensual ajustado a siete columnas, navegación Patient 360 sin tira horizontal y odontograma por cuadrante seleccionable en móvil. El barrido E2E de rutas comprueba que documento y contenedores operativos no desborden a 320/390 px. Capturas de agenda Mes, pacientes y odontograma a 390 px inspeccionadas. Los formularios e historiales largos siguen requiriendo scroll vertical normal.
- TypeScript: los 46 archivos de aplicación y pruebas en `frontend/src` se migraron a `.ts/.tsx`; `index.html`, Tailwind y Vitest apuntan a esas extensiones. Se añadieron `tsconfig.json`, `npm run typecheck`, contratos de dominio, API genérica tipada y `useResource<T>` para GET por ID con descarte de respuestas al cambiar de ruta. Dashboard, historial, detalle/edición, nueva consulta y carga de imagen reutilizan este hook. El tooling de Vite/Playwright permanece en JavaScript. `strict: true` y `noImplicitAny: true` están activos y pasan; las respuestas API tipadas siguen siendo contratos estáticos, no validación runtime.
- Toasts: proveedor global accesible con roles `status`/`alert`, cierre manual y caducidad; los resultados transitorios de alta, edición, guardado, borrado, correo, análisis y login se anuncian fuera de la sección. Un éxito tras reintento retira errores anteriores. Las validaciones se mantienen junto al campo y los errores persistentes de GET con reintento siguen en contexto. Unit test verifica error → éxito → cierre.
- Arquitectura: contratos en `types/domain.ts`, transporte en `api/client.ts`, carga repetida de detalle/edición en `hooks/useResource.ts`, vistas orientadas a composición. Otras páginas siguen con lógica específica dentro de la vista; extraerla requiere revisar cada flujo y no se declara terminada.
- Gates tras los cambios: `npm run typecheck` con `strict: true`, `npm run lint`, `npm test` (5/5), `npm run build` y Playwright (3/3) pasaron tras agregar 360 px al barrido, mover el toast móvil al borde inferior y extraer las cargas de nueva consulta e imagen. El E2E comprobó posición y reintentos; la captura del toast fue inspeccionada. Un primer E2E tras activar strict falló por la aserción del visor que incluía imágenes internas sin URL; se acotó a recursos con `src` y la suite siguiente pasó 3/3.
- Pendiente: aislar lógica de carga/mutación restante cuando exista patrón común y revisar visualmente más combinaciones de datos y estados. La validación final general de la fase previa permanece pospuesta por petición del usuario.
