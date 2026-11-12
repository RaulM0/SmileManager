# Auditoría del lenguaje visual y los botones

## Alcance y método

Auditoría del frontend React existente, sin cambios de código. Se revisaron las rutas de `frontend/src/App.tsx`, páginas, componentes, estilos globales, configuración Tailwind, dependencias y documentación previa. Se inspeccionaron capturas de la ejecución E2E anterior a 390 y 1280 px de inicio, agenda, ficha, antecedentes y odontograma. Son capturas de datos sintéticos, no investigación con usuarios. Además se midieron estilos calculados en Chromium con el CSS de producción existente y elementos de prueba; no se alteró la aplicación.

Los nombres de patrones y juicios de percepción son **interpretaciones de diseño**, no etiquetas oficiales de un framework ni resultados de pruebas con personal clínico. El análisis de estilos calculados se limita a Chromium y al CSS compilado disponible; deben verificarse los demás navegadores. El censo es estático, no cuenta elementos que se generan en cada iteración ni pretende contar botones visibles en ejecución. La aplicación también conserva plantillas Django y controles de terceros: no se confunden con la SPA React.

## 1. Patrón actual

**Dominante en React: interfaz operativa empresarial densa, de superficie plana y minimalismo clínico**. El producto completo combina además pantallas Django heredadas de estilo Bootstrap. No es una implementación pura de Material, Fluent ni un framework de diseño concreto. Mezcla:

- **Flat enterprise:** superficies blancas, canvas gris, bordes finos, radio de 4–6 px, poca sombra y acento teal. La jerarquía se consigue mediante tipografía y agrupación; `app.css:5–21, 100–145`.
- **Data-dense enterprise / workspace:** shell con barra superior y navegación lateral, contexto persistente del paciente, agenda y tablas compactas; `AppLayout.tsx`, `PatientWorkspaceNav.tsx`, `AppointmentsPage.tsx`, `app.css:55–61, 196–241`.
- **Convenciones visuales Bootstrap-like y nativas:** iconos Bootstrap, botones rectangulares primarios/contorneados y algunas clases heredadas; **Bootstrap CSS no figura en las dependencias ni se importa**. Los estilos por defecto del navegador influyen realmente en los botones, por el preflight desactivado.
- **Patrones específicos de dominio:** diagrama de superficies dentales, selección de estados, expediente y línea de consultas. No todo es un dashboard ni una colección de tarjetas.
- **Django legacy: Bootstrap real y estilos de página propios.** `Home/templates/Dentista/base.html` carga Bootstrap 5.3.3 desde CDN y define navbar con gradiente, sombra, blur y animación. `Pacientes/templates/consentimiento/consentimiento.html` añade radio de 15 px, elevación y `translateY(-2px)` al hover; el odontograma legacy define otra paleta, sombras y tipografía. Por tanto, en el producto completo sí conviven estética Bootstrap, componentes planos React y estilos decorativos heredados.

En React no se observan neumorfismo, skeuomorfismo, glassmorphism o un sistema Material/Fluent completo; el `backdrop-filter` de la navbar legacy es una excepción técnica concreta, no un sistema glassmorphism integral. Existen paneles y resúmenes, pero no una composición bento dominante. Inter es la primera opción tipográfica de React, pero no se ha observado una carga propia: puede utilizarse el fallback del sistema.

**Consistencia: media en React; baja al considerar React y Django legacy juntos.** Existe una paleta, CSS y documentación común para React (`docs/frontend-redesign/03-DESIGN-SYSTEM.md`), con diferencias de implementación, dimensiones y estados. No hay un contrato de componentes ni una correspondencia única entre intención y apariencia. `clinical-action-outline` sirve para reintentar, buscar, cambiar paciente, navegar, limpiar y paginar; `clinical-action-primary` identifica tanto acción como filtro elegido. Se han observado elementos con y sin borde efectivo usando la misma clase.

## 2. Mapa de pantallas y controles

| Área real                           | Lenguaje y controles observados                                                          | Riesgo para una migración global                                                                  |
| ----------------------------------- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| Login                               | Formulario plano; submit teal; icono de revelar contraseña integrado en campo            | Mantener visibilidad de contraseña, nombre y estado.                                              |
| Shell, sidebar y cabecera           | Navegación lateral con fondo tintado activo; botón de menú y salida transparentes        | Navegación, cierre de sesión y foco del drawer no son acciones de formulario.                     |
| Inicio                              | Franja de datos y tablas de citas; enlaces y acción de reintento                         | Los accesos y los datos operativos tienen distinto peso.                                          |
| Agenda/listado de citas             | Filtros por estado, búsqueda, calendario, agenda móvil, acciones por fila y confirmación | Filtro seleccionado no es una acción primaria; preservar URL, estados y confirmación.             |
| Alta/edición/detalle de cita        | Selector de paciente, formularios, navegación, acciones de guardar y volver              | Mantener borradores, validación, precarga y disabled.                                             |
| Pacientes/lista/búsqueda/contacto   | Búsqueda, tabla, paginación, formularios, enlaces y desactivación                        | Paginación y links mantienen semántica; no suprimir acciones por densidad.                        |
| Expediente y ficha                  | Navegación local de rutas, lista de tareas, resumen y accesos                            | La navegación con apariencia de pestaña sigue siendo navegación entre URL.                        |
| Antecedentes y consultas/receta     | Radios visuales, campos, submit, historial y descarga/impresión                          | Preservar el estado clínico neutral y la semántica de radio.                                      |
| Odontograma                         | Selector de herramienta, cuadrantes móviles, 52 posiciones y superficies clicables       | No aplicar un botón genérico a cada superficie: geometría, selección y leyenda son clínicas.      |
| Imágenes, progreso y consentimiento | Carga, filtros, descarga, eliminación, estudio y aceptación                              | No tratar enlaces de descarga como botones deshabilitados nativos; conservar feedback y permisos. |
| Diagnósticos IA                     | Listado, filtro, visor y análisis explícito                                              | No introducir procesamiento al consultar; el visor usa controles de OpenSeadragon.                |
| Exportaciones y privacidad          | Enlaces de descarga y contenido informativo                                              | Una descarga no equivale a navegación cualquiera.                                                 |

No se encontró pantalla React de configuración en las rutas actuales. El inventario incluye el selector de expediente y los hubs de pacientes e imágenes. La existencia de páginas Django separadas no implica que estén cubiertas por un futuro componente React.

## 3. Inventario técnico cuantificado

Método reproducible: búsqueda textual en todos los `frontend/src/**/*.tsx` excepto `*.test.tsx`, contando aperturas JSX de `<button`, `<Button`, `<Link` y `<NavLink`; se consideran enlaces estilizados aquellos con `clinical-action-*`, `clinical-form-submit` o `clinical-icon-action` en su apertura. No se cuentan elementos renderizados por mapas, HTML de librerías ni enlaces `<a>` dentro del número de React Router. Las menciones de clase se cuentan por texto, **no por instancia ni variante visual única**.

| Inventario estático                               |                                                      Cantidad |
| ------------------------------------------------- | ------------------------------------------------------------: |
| Aperturas JSX `<button>`                          | 66 en 28 archivos; algunas generan muchos controles con `map` |
| Usos `<Button>`                                   |               0; no se encontró un componente global `Button` |
| Aperturas `<Link>` / `<NavLink>`                  |                                                            36 |
| De esos, enlaces con clases compartidas de acción |                                                            19 |
| Aperturas `<a>`                                   |                   5; incluyen descargas, no todas son botones |
| Atributos `aria-pressed` en código                |                6 expresiones; varias generan grupos completos |
| `role="tab"` en JSX inspeccionado                 |                     0; la navegación del paciente son enlaces |
| CSS Modules en `frontend/src`                     |                                                             0 |

Menciones textuales en JSX: `clinical-action-outline` 49; `clinical-action-primary` 15; `clinical-form-submit` 9; `clinical-action-compact` 13; `clinical-action-danger` 4; `clinical-action-success` 1; `clinical-icon-action` 2; `odontogram-state-button` 1. Las clases pueden combinarse y aparecer en expresiones condicionales, por lo que **no deben sumarse como botones únicos**. Hay además botones de shell, selector de pacientes, toast, login, calendario y odontograma con estilos propios, así como radios nativos estilizados y controles generados por OpenSeadragon.

Las 66 aperturas no son 66 apariencias ni 66 acciones visibles: por ejemplo una apertura en `Tooth` genera cinco superficies por pieza y otra genera filtros de agenda. `PatientForm`, `AppointmentForm`, `ConfirmDialog` y `PatientWorkspaceNav` reutilizan estructura específica, pero no encapsulan todas las acciones. `frontend/tailwind.config.cjs` usa Tailwind 3.4 con prefijo `co-`, `preflight: false`, tokens de color y fuente; `frontend/src/styles/app.css` contiene `@apply`, CSS convencional, media queries y valores de color repetidos. No hay CSS Modules. `bootstrap-icons` sí se importa; CSS de Bootstrap no.

En las 38 plantillas HTML legacy localizadas en `Home`, `Citas`, `Pacientes`, `Sesiones` y `DiagnosticosIA`, excluyendo correos, la búsqueda textual encuentra 65 aperturas `<button>`, 175 `<a>`, 38 menciones de `btn-primary` y 171 de `btn-outline-*`. Estas cifras incluyen código y estilos inline, no equivalen a controles visibles ni distinguen rutas activas o plantillas extendidas. Ejemplos: radios de antecedentes usan `btn-outline-success/danger/secondary`, agenda usa botones Bootstrap, diagnósticos incluye botones y modal, consentimiento redefine `.btn-primary` y `.btn-outline-secondary`. Los estilos provienen del CDN y overrides locales, no del CSS de React. La inspección legacy es estática y representativa: no se ha comprobado visualmente cada ruta ni estado de esas plantillas.

## 4. Inventario de variantes visuales

El número útil es **12 familias de presentación identificables**, no un número cerrado de combinaciones renderizadas. Tamaños Tailwind indicados según escala por defecto; `min-height` no equivale siempre a altura real. Pueden combinarse modificadores y clases utilitarias.

| Familia / usos                                | Reglas principales y estados observados                                                                                                                                                                                                                                                                  |
| --------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1. Primaria sólida `clinical-action-primary`  | Teal `#176b78`, texto blanco 14 px/600, `min-h-9` 36 px, padding 8×12, `co-rounded` 4 px, borde transparente; hover `#105763`, disabled gris; sin sombra propia ni `:active` de producto. Se usa también para filtro seleccionado.                                                                       |
| 2. Envío `clinical-form-submit`               | Misma familia teal, 14 px/600, mínimo 40 px, padding 8×16; transición de colores y spinner en ciertos formularios. No equivale exactamente a la primaria anterior.                                                                                                                                       |
| 3. Secundaria `clinical-action-outline`       | Blanco, texto teal 14 px/500, borde declarado `#a8c7cb`, mínimo 36 px, padding 8×12, radio 4 px; hover tinte `#e8f3f4`; disabled gris. El borde real depende del tipo de elemento, ver §5.                                                                                                               |
| 4. Compacta `clinical-action-compact`         | Modificador: mínimo 32 px, padding 4×8, 12 px; se combina con primaria o secundaria. No es color/acción independiente.                                                                                                                                                                                   |
| 5. Éxito contextual `clinical-action-success` | Blanco, borde verde `#83b89b`, texto `#1d6848`, 12 px/500, mínimo 32 px, padding 4×8; hover verde pálido. Completar cita.                                                                                                                                                                                |
| 6. Destructiva `clinical-action-danger`       | Blanco, texto y borde rojo Tailwind, 12 px/500, mínimo 32 px, padding 4×8, hover rojo claro y disabled; aparece en fila y confirmación. El `focus-visible` global con `!important` puede prevalecer sobre el rojo declarado.                                                                             |
| 7. Icono contorneado `clinical-icon-action`   | 32×32 px, blanco, borde teal pálido, icono teal; hover y foco; revisar nombre accesible en cada uso. Flechas de calendario usan otra clase `clinical-calendar-nav`, de 36×36.                                                                                                                            |
| 8. Ghost/contexto                             | `.workspace-logout`, `.workspace-menu-toggle`, `.clinical-calendar-today`, `.login-password-toggle`, cierre de toast: transparentes o blancos y bordes distintos; no son una variante centralizada. Hoy aparece como enlace textual; el cierre de toast es 24×24.                                        |
| 9. Enlaces de acción                          | `<Link>`/`<a>` con clases de acción, y enlaces textuales de tablas o navegación. `a.clinical-action-primary` fuerza texto blanco. Las anclas no admiten `disabled` nativo; algunas descargas usan `aria-disabled` y lógica propia.                                                                       |
| 10. Filtros y vistas                          | Estado de cita alterna clases primaria/outline; Agenda/Mes usa outline compacta y `[aria-pressed=true]` tintada; radios y cuadrantes tienen otras reglas. No existe componente común de selección exclusiva.                                                                                             |
| 11. Selección de antecedentes                 | `clinical-radio-choice`: blanco, borde sólido `#cbd5d9`, mínimo 42×32, 12 px, padding 5×8; `:checked` cambia borde/fondo/peso para sí, no y desconocido. Input radio real oculto visualmente con foco delegado al label.                                                                                 |
| 12. Odontograma                               | Herramientas `odontogram-state-button`: borde sólido gris, 36 px mínimo, 12 px, 550; activa teal tintado/700. Cuadrantes móviles son botones de 36 px/11 px con `aria-pressed`. Superficies: 24×24 escritorio, 32×32 móvil, borde sólido o discontinuo y colores clínicos; son controles especializados. |

Los iconos son `bootstrap-icons` en la mayoría de JSX, a veces ocultos a tecnología asistiva con `aria-hidden`; OpenSeadragon aporta sus propias imágenes y controles. No hay evidencia de sombras internas o externas aplicadas por el CSS de estas familias compartidas; sí hay sombras en overlays, drawer y toast. Los controles generados por bibliotecas y el selector nativo de archivo necesitan evaluación propia.

## 5. Por qué algunos se ven hundidos: resultado comprobado

**Hecho técnico medido:** con CSS compilado actual, Chromium calculó para `<button class="clinical-action-outline">` `border-style: outset`, ancho 1 px, fondo blanco, `box-shadow: none`, `appearance: auto`, radio 4 px y altura 38 px. Para `<a class="clinical-action-outline">` calculó `border-style: none`, ancho 0 px y altura 36 px. Con `clinical-action-primary`, el `<button>` también calculó `outset`, aunque el borde es transparente. El selector propio `.odontogram-state-button`, que declara `border: 1px solid`, calculó `solid`. El experimento utilizó el mismo CSS de `frontend/dist`, sin estado hover y sin modificaciones del proyecto.

La causa rastreable es la combinación de `corePlugins: { preflight: false }` en `tailwind.config.cjs`, `button, input, select, textarea { font: inherit; }` en `app.css:24` sin normalización de bordes, y `co-border`/`co-border-[#a8c7cb]` en `app.css:49`: se declaran anchura y color, pero no `border-style: solid`. El estilo nativo del navegador completa la regla. En Chromium, `outset` dibuja bordes con iluminación/sombreado y puede generar la percepción de relieve o botón presionado; en las capturas de agenda se aprecia un contorno claro/oscuro. La misma clase en un enlace pierde el contorno. Esto es una **diferencia objetiva**; cuánto la interpreta una persona como «hundida» requiere pruebas con usuarios y otros navegadores.

También contribuyen potencialmente: muchos controles pequeños y contorneados agrupados; borde de color cercano al acento, sobre fondo blanco; estados seleccionados compartiendo lenguaje con acciones (filtro teal frente a «Nueva cita» teal); y diferencias pequeñas entre tintes de hover y seleccionado en Agenda/Mes, radios y herramientas. El fondo gris del canvas hace más visibles las cajas blancas. Los estilos CSS revisados no sustentan atribuirlo a `inset box-shadow`: no existe tal sombra en la familia compartida. La ausencia de una sombra externa tampoco demuestra por sí sola una sensación hundida.

## 6. Semántica y jerarquía

| Control real                                    | Implementación actual                                                                                                             | Lectura UX / opción conceptual                                                                                                                                                                                                                                                                                     |
| ----------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `Todas / Pendientes / Completadas / Canceladas` | `role=group`, botones `aria-pressed`; cambian parámetros y filtran el mismo contenido. Seleccionado usa `clinical-action-primary` | Es un **filtro de selección exclusiva**, no cuatro acciones ni necesariamente tabs. Un grupo de filtros o segmented control con selección textual clara reduce la competencia con «Nueva cita». Puede conservar botones y `aria-pressed` o estudiarse radio group; no cambiar semántica sin definir teclado y URL. |
| `Agenda / Mes` móvil                            | Botones `aria-pressed`, dos vistas de la misma agenda                                                                             | Selector de vista exclusivo; segmentado o tabs si se implementa el patrón completo de paneles y teclado. No basta con añadir `role=tab`.                                                                                                                                                                           |
| Cuadrantes del odontograma                      | Grupo de botones con `aria-pressed`, solo móvil                                                                                   | Selector exclusivo de parte del diagrama; se puede presentar como segmentado adaptativo, manteniendo orden y nombres anatómicos.                                                                                                                                                                                   |
| `Sin registrar / Sí / No`                       | Radios nativos y labels con apariencia de botones                                                                                 | Ya son radios semánticamente: preservar el comportamiento de selección y estado desconocido. El problema es visual, no que deban reemplazarse por botones.                                                                                                                                                         |
| Herramientas del odontograma                    | Botones `aria-pressed` que seleccionan cómo pintar                                                                                | Selección de herramienta persistente, no acción de guardar ni estado de superficie; podría ser toolbar/radio según diseño probado.                                                                                                                                                                                 |
| Secciones del paciente                          | `nav` + `NavLink`, subrayado activo                                                                                               | Navegación entre rutas con apariencia de pestañas. Mantener enlaces y `aria-current` de NavLink; no convertir automáticamente en ARIA tabs.                                                                                                                                                                        |
| `Volver`, `Ver`, `Editar`, descarga             | Enlaces y botones según destino/acción                                                                                            | Navegar conserva enlace real; guardar, borrar o abrir diálogo usa botón. La descarga requiere contrato accesible de progreso.                                                                                                                                                                                      |
| Botones de superficies dentales                 | Botones con nombre pieza/superficie/estado                                                                                        | Diagrama interactivo especializado; no tratar como variantes normales.                                                                                                                                                                                                                                             |

La jerarquía existe parcialmente: primaria teal, secundaria contorneada, destrucción roja y compactas. Ghost, icon-only y enlaces se resuelven por estilos separados; no existe una escala formal aplicada de manera uniforme. Un ejemplo verificable: en agenda el filtro elegido y «Nueva cita» comparten `clinical-action-primary`; uno representa estado persistente y el otro inicia una tarea. En confirmaciones el peligro es rojo, pero comparte el tamaño compacto de acciones de fila, mientras «Volver» es un outline de mayor altura: conviene evaluar la jerarquía contextual sin asumir que el peligro siempre debe dominar.

## 7. Estados interactivos y accesibilidad

| Estado                          | Evidencia / límite                                                                                                                                                                                                                                          |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Default                         | Colores y tamaños comunes; `outset` nativo en Chromium para botón compartido y diferencia con enlace.                                                                                                                                                       |
| Hover                           | Primaria oscurece, outline recibe tinte, herramienta y radio usan gris claro; no todos los controles tienen la misma transición. Hover no existe en todos los dispositivos.                                                                                 |
| Active / presionado transitorio | No se encontró una regla de producto `:active` equivalente en las familias compartidas; el navegador puede aportar comportamiento propio. No se debe confundir `:active` con selección persistente.                                                         |
| Seleccionado                    | Filtro usa primaria; Agenda/Mes, cuadrante y herramientas utilizan tinte/borde; radios usan `:checked`. Expresiones `aria-pressed` existen, pero la apariencia no es uniforme.                                                                              |
| Focus                           | Regla global `:focus-visible` de 2 px teal con offset 2 px e `!important`; radios transfieren foco al label. La regla global puede anular el color de foco de la variante destructiva. Debe verificarse recorte de outline y contraste en todos los fondos. |
| Disabled                        | Familias principales definen fondo y texto; `clinical-icon-action` no tiene regla específica. Anclas requieren control y semántica propios; no basta con `aria-disabled` para bloquear.                                                                     |
| Loading                         | Algunos submit usan `clinical-form-spinner` y texto, otros cambian etiqueta o solo `disabled`; no existe contrato común. El bloqueo puede venir de un `fieldset`.                                                                                           |
| Movimiento reducido             | Regla global reduce transiciones y animaciones a `.01ms`; comprobar que cada estado de carga conserve una señal textual.                                                                                                                                    |

El diseño futuro debe comprobar contrastes de texto, límites y estados según [WCAG 2.2: contraste no textual](https://www.w3.org/TR/WCAG22/#non-text-contrast), foco y teclado; el tamaño mínimo AA de objetivos es 24×24 CSS px con excepciones, no una garantía de comodidad táctil ([WCAG 2.2, 2.5.8](https://www.w3.org/TR/WCAG22/#target-size-minimum)). La separación y los objetivos dentales merecen prueba real. Los 32 px móviles no son automáticamente un incumplimiento. Para verdaderas tabs, aplicar roles, relación con panel y manejo de teclado descritos por [WAI-ARIA APG](https://www.w3.org/WAI/ARIA/apg/patterns/tabs/). Ninguna revisión aquí certifica conformidad WCAG o prueba con lector de pantalla.

## 8. Opciones de evolución — propuestas, no cambios implementados

Las cuatro opciones conservan la paleta y densidad actuales. Las duraciones son rangos iniciales para prototipos, no promesas ni tokens aprobados. En todas, foco visible independiente del hover y estado seleccionado reconocible sin animación; cualquier movimiento se suprime con `prefers-reduced-motion`.

### A. Flat / minimal enterprise

- **Aspecto y cambio:** superficies planas, contornos `solid` normalizados, jerarquía por relleno, texto y espacio; diferenciar filtros de acciones. Mantiene radios 4 px y sombras solo en overlays.
- **Hover:** cambio leve de fondo/borde; **pressed:** oscurecer brevemente sin movimiento; **focus:** anillo exterior de 2 px con separación; **sombra:** ninguna en reposo.
- **Ventajas:** continuidad y lectura clara, poco coste visual; densidad estable. **Desventajas:** menor sensación de relieve; límites de controles deben seguir siendo perceptibles.
- **Compatibilidad/esfuerzo:** alta; ajuste CSS compartido y revisión de controles propios y elementos nativos. No se propaga automáticamente a todos.

### B. Flat 2.0 con elevación funcional mínima

- **Aspecto y cambio:** igual que A, pero sombra exterior muy suave de 1 px en botones de acción seleccionados por jerarquía, no en cada filtro/superficie dental; 4–5 px de radio.
- **Hover:** cambio de fondo y, si aporta señal, sombra algo más visible; **pressed:** eliminar sombra y oscurecer o bajar 1 px; **focus:** anillo exterior independiente de sombra; **sombra:** baja y consistente.
- **Ventajas:** puede reforzar affordance y diferencia de pulsación. **Desventajas:** acumulación de ruido en tablas y riesgo de parecer más «hundido» si se ejecuta mal; requiere prueba comparativa.
- **Compatibilidad/esfuerzo:** media-alta; además de normalización exige reglas por contexto y combinación con foco/disabled.

### C. Enterprise inspirado en Fluent, sin adoptar Fluent

- **Aspecto y cambio:** controles de superficie neutra y borde discreto, contraste de interacción mediante fondo; acento reservado para acción y selección, radio 4–6 px.
- **Hover:** fondo neutro o teal tenue; **pressed:** fondo más marcado sin desplazamiento; **focus:** anillo bien contrastado; **sombra:** ninguna o reservada a overlays.
- **Ventajas:** separa acciones primarias de navegación/selección y funciona en áreas densas. **Desventajas:** una adaptación parcial sin reglas puede introducir otra familia inconsistente; no equivale a adoptar el sistema de Microsoft.
- **Compatibilidad/esfuerzo:** media-alta; requiere redefinir secundarios, filtros y estados en varias pantallas, sin cambiar necesariamente comportamiento.

### D. Soft enterprise de bajo contraste decorativo

- **Aspecto y cambio:** secundarios con superficie teñida muy ligera y borde controlado, primarios sólidos, menos cajas destacadas; radio 4–6 px. «Soft» describe tintes, no neumorfismo.
- **Hover:** tinte más visible; **pressed:** cambio de tono; **focus:** anillo exterior; **sombra:** ninguna o casi imperceptible.
- **Ventajas:** reduce la repetición de contornos y puede dar jerarquía tranquila. **Desventajas:** el tintado podría parecer selección permanente y debe diferenciarse de los estados clínicos; contraste del límite debe medirse.
- **Compatibilidad/esfuerzo:** media; requiere validar selección, fondos y semántica en agenda, odontograma y antecedentes.

## 9. Comparativa cualitativa

Las evaluaciones indican consecuencias esperadas frente a esta implementación; no son puntuaciones ni resultados medidos.

| Alternativa           | Profesionalismo y claridad previstos                           | Modernización                    | Cambio requerido                                      | Compatibilidad actual                                    |
| --------------------- | -------------------------------------------------------------- | -------------------------------- | ----------------------------------------------------- | -------------------------------------------------------- |
| A Flat enterprise     | Sobrio y claro si límites y estados contrastan                 | Discreta, centrada en coherencia | Menor: normalización, tokens y controles de selección | Alta: mantiene estructura y superficies planas           |
| B Flat 2.0            | La profundidad puede aclarar acción; exceso produce ruido      | Visible pero sutil               | Medio: normalización más sombras según contexto       | Media-alta: overlays ya tienen sombra, acciones no       |
| C Inspirado en Fluent | Neutros pueden distinguir mejor acción, navegación y selección | Moderada                         | Medio: redefinir jerarquía y estados                  | Media-alta: paleta y densidad compatibles                |
| D Soft enterprise     | Calma visual si selección se diferencia del tinte              | Moderada                         | Medio: revisar contraste y semántica clínica          | Media: tintes ya existen, pero también señalan selección |

**Compatibilidad técnica no es elección de producto:** A precisa menos cambio visual inicial; no se selecciona una alternativa sin comparar prototipos y aprobarla.

## 10. Microinteracciones posibles

| Efecto               | Utilidad y condiciones                                                                                                                                                                                              |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Hover de fondo/borde | Apropiado en las cuatro opciones; usar cambio discreto solo en dispositivos con hover. No depender de él para descubrir acciones.                                                                                   |
| Elevación            | Solo opción B y solo si clarifica jerarquía; probar en fondos blanco/gris y sin ocultar foco. Evitar sombra en cada celda dental.                                                                                   |
| `translateY(1px)`    | Posible en B como respuesta transitoria; puede mover texto y resultar molesto en acciones repetidas. No mover layout ni usar para selección persistente.                                                            |
| `scale(0.98)`        | No se recomienda como comportamiento global: reduce objetivo visual y puede desestabilizar tablas/odontograma; tendría que demostrarse una ventaja específica.                                                      |
| Transición           | Inicialmente 100–150 ms de color/borde y, si se aprueba, sombra/transform; sin transiciones de layout ni demora en respuesta. Reducir movimiento.                                                                   |
| Focus                | Mantener foco visible de teclado, 2 px como base y separación suficiente; comprobar contraste, clipping, modo de alto contraste y coexistencia con hover/selección. No sustituirlo por una sombra tenue.            |
| Loading              | Mantener etiqueta o texto de progreso, desactivar doble envío cuando proceda, conservar ancho para evitar saltos y exponer estado; spinner opcional y no única señal. No sustituir errores junto a campo por toast. |

## 11. Sistema futuro conceptual

Separar **semántica de elemento**, intención y densidad; no imponer la misma geometría al diagrama clínico:

```text
ActionButton: primary / secondary / tertiary / destructive
  tamaños regular y compacto; icono opcional; pending / disabled
IconButton: nombre accesible obligatorio, objetivo y foco definidos
ActionLink: navegación o descarga real, aspecto por intención sin fingir disabled nativo
FilterGroup / FilterChip: selección exclusiva o múltiple según tarea
ViewSwitcher: vista seleccionada; tabs solo cuando exista tablist/tabpanel real
RadioGroup: preguntas clínicas y respuestas mutuamente excluyentes
PatientNavigation: enlaces de rutas y aria-current
DentalToolSelector / DentalSurface: controles de dominio con reglas y pruebas propias
```

Las variantes son categorías propuestas, no una API definitiva. Un `Button` futuro debe recibir `type` explícito o seguro, permitir `ref`, estado de envío y nombres accesibles, preservar submit y disabled; no cambiar silenciosamente `<a>` a `<button>`. Tokens posibles: color por intención/estado, borde explícito, radio, altura, padding, icono, foco y movimiento. Una capa de clases compartidas puede ser suficiente inicialmente, pero un componente solo no corregiría todos los controles especializados ni los enlaces existentes.

## 12. Riesgos y plan de evaluación posterior

1. **Regresión visual por normalización:** cambiar border-style/appearance altera botón y enlace de manera distinta; verificar tamaños calculados, saltos y especificidad, sin activar preflight global a ciegas.
2. **Regresión funcional:** preservar `type`, `onClick`, submit, disabled, `aria-pressed`, URL/query, popups, guardias, descarga, confirmación y lógica de permisos. No rehacer el visor de terceros ni plantillas Django por accidente.
3. **Jerarquía y estado clínico:** no confundir «Sin registrar» con respuesta negativa ni convertir un filtro seleccionado en acción destructiva. Mantener textos y estados odontológicos.
4. **Accesibilidad y responsive:** revisar 320/390/768/1280, zoom, objetivo, contraste, teclado y lector de pantalla; probar foco dentro de diálogos y tablas, enlaces con `aria-disabled` y `prefers-reduced-motion`.
5. **Alcance:** inventariar también formularios y pantallas Django legacy y controles de OpenSeadragon antes de prometer cobertura global. Preparar matriz de capturas y estados por variante. No hay estimación fiable en días sin prototipo, navegador/rol objetivo y alcance acordados.

**Conclusión:** hay base compartida, pero no un punto único de sustitución. La complejidad es **media para normalizar la familia común y media-alta para lograr cobertura integral**: hay 66 aperturas de botón, 19 enlaces de Router con apariencia de acción, controles generados dinámicamente y componentes especializados. La prioridad posterior es acordar la dirección visual y validar muestras de cada tipo antes de migrar por etapas. No se han cambiado estilos ni componentes en esta auditoría.
