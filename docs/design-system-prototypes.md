# Laboratorio de prototipos del sistema de diseño

## Acceso y alcance

Ruta autenticada `/design-system` en el servidor de desarrollo de Vite; en la instalación de producción con `basename: /app`, `/app/design-system`. La carga es diferida y el laboratorio no aparece en la navegación de producción. Usa datos y estado locales: ningún control consulta la API ni modifica pacientes o citas. Las acciones muestran feedback de demostración; el botón «Guardar cambios» simula carga durante 1,6 segundos.

El CSS vive en `frontend/src/design-system/design-system-lab.css` y está delimitado por `.dsl-lab` o clases exclusivas `dsl-*`. No activa Tailwind Preflight ni reemplaza clases productivas. Los botones y controles de selección del prototipo definen `appearance` y `border-style: solid` expresamente; no dependen del borde nativo `outset` detectado en la auditoría. La SPA y las plantillas Django conservan sus controles originales.

Se comparan las mismas acciones, filtros exclusivos, vista, tabs de ejemplo, radios clínicos, estados y acciones compactas. Cada alternativa dispone de una composición de agenda independiente con filtros funcionales; los datos son ficticios. «Mes» cambia la etiqueta de la representación, no implementa un calendario real. Las tabs de ejemplo usan el patrón tablist/tabpanel y flechas; la navegación del expediente real sigue siendo un conjunto de enlaces.

## A — Flat Enterprise

Superficies blancas, bordes sólidos, acento teal y selección principalmente por subrayado. Hover y pulsación cambian tono sin elevación ni desplazamiento; radio 4 px. Ventaja: cercanía con la identidad existente y buena densidad. Riesgo: contornos repetidos y affordance más discreta. Migración: normalizar bordes, definir jerarquías y separar filtros de acciones, además de revisar elementos especializados.

## B — Flat 2.0 con elevación mínima

Conserva la estructura plana, con sombra de 1 px para acciones, sombra algo mayor en hover y desplazamiento de 1 px únicamente durante `:active`; seleccionado no usa desplazamiento permanente. Radio 5 px. Ventaja: respuesta táctil perceptible con baja profundidad. Riesgo: ruido en controles repetidos y percepción de relieve si la sombra se acentúa. Migración: además de normalizar controles, decidir qué contextos admiten elevación y validar estados combinados.

## C — Enterprise inspirado en Fluent

Superficies secundarias neutras, bordes más suaves y fondos diferenciados para interacción y selección; no utiliza ni copia componentes Fluent. Radio 5 px y sin desplazamiento. Ventaja: jerarquía menos dependiente de contornos y estados explícitos. Riesgo: controles neutros pueden perder reconocimiento si el contraste es insuficiente. Migración: revisar tokens de interacción, jerarquía de secundarios y estados de selección.

## D — Soft Enterprise

Secundarios en tintes suaves y radio 7 px; selección con tinte y un indicador, sin sombras neumórficas ni movimiento decorativo. Ventaja: menor dureza visual en operaciones repetidas. Riesgo: confundir tintes de reposo y selección o con estados clínicos. Migración: validar contraste y evitar reutilizar colores de selección como diagnósticos.

## Interacción y accesibilidad

Las cuatro opciones tienen hover, `:active` transitorio, foco visible, disabled y ejemplos seleccionados; la carga usa texto y spinner, sin depender del movimiento. Los filtros y vistas son botones con `aria-pressed`; antecedentes usan radios nativos. Los badges son texto no interactivo. El foco y el tamaño deben probarse en dispositivos reales; la compatibilidad WCAG no se certifica con este prototipo. `prefers-reduced-motion` reduce duración de animación/transición. Los iconos proceden de Bootstrap Icons ya instalado.

## Propuestas de cajas de texto

El laboratorio también compara cuatro opciones independientes de las alternativas A–D de botones: **1 Contorno preciso** (blanco y borde definido), **2 Flat 2.0** (borde suave y sombra exterior mínima), **3 Superficie suave** (tinte tenue y radio moderado) y **4 Línea de acento** (fondo claro y borde inferior más marcado). Todas normalizan el borde con `solid` y permiten probar foco, contenido, error corregible y estado deshabilitado. Se eligió la **opción 2**, aplicada a los controles React compartidos `.clinical-form-control`, incluidos inputs, selects y áreas de texto, manteniendo sus controles nativos y validaciones. Las muestras del laboratorio siguen siendo independientes. Las plantillas Django legacy tienen estilos separados. El contraste y comportamiento entre navegadores requieren revisión.

## Selección aplicada a React

Se eligió B para acciones, filtros de agenda, selector de vista, acciones contextuales y agenda; D para navegación local y respuestas clínicas. La implementación usa estilos compartidos de React, borde sólido explícito, sombra y pulsación discretas, filtros diferenciados de acciones y controles de respuesta con indicador de selección. Conserva radios, enlaces, `aria-pressed`, rutas y lógica existentes. El laboratorio sigue disponible para comparación. Las plantillas Django legacy y el visor de terceros tienen estilos independientes y no se han migrado con estas reglas.

Sigue pendiente probar contraste y teclado/lector de pantalla en diferentes navegadores y validar con profesionales. El trabajo clínico histórico pendiente continúa fuera de este cambio.

## Validación realizada

- `npm run lint`, `npm run typecheck`, `npm test` (21 pruebas, incluidas tres del laboratorio) y `npm run build`: correctos.
- Chromium con sesión simulada: ruta de laboratorio y ruta existente de privacidad renderizadas; navegación con flechas en tabs; `border-style` calculado `solid` en los botones del laboratorio; sin desbordamiento horizontal del documento a 320, 360, 390, 768, 1280 y 1600 px. Se inspeccionaron capturas de escritorio y móvil.
- Firefox y WebKit no estaban instalados en el entorno; Edge y Safari tampoco se probaron. La normalización explícita reduce la dependencia de estilos nativos, pero la equivalencia entre navegadores queda pendiente de comprobación. No se realizaron pruebas con lector de pantalla ni usuarios clínicos.
- Tras aplicar la selección en React: lint, typecheck, 21 pruebas y build correctos; recorrido Playwright 3/3 con base aislada, e inspección visual móvil de agenda y antecedentes. Posteriormente se ajustó solo el color de confirmación destructiva, se repitió el build y se comprobó en Chromium el borde sólido en botón/enlace y el color de esa confirmación. El recorrido completo no se repitió después de ese último ajuste CSS.
