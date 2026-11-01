# Accesibilidad

## Criterios

- Navegación semántica, landmarks `header/nav/main/footer`, skip link, heading order.
- Ruta activa visual y `aria-current=page`; foco visible; navegación por teclado; drawer móvil con nombre, estado, foco inicial, contención Tab/Shift+Tab, cierre Escape y retorno del foco.
- Labels explícitas, errores asociados con `aria-describedby`, required y estados disabled claros.
- Botones icon-only con nombre accesible; tooltip no sustituye nombre.
- Estado textual además de color; targets táctiles para controles de dientes.
- Formularios reportan éxito/error mediante región `aria-live`; error no depende solo del color.
- Tablas con `caption`/headers semánticos cuando adecuado; overflow táctil.
- Diálogos de confirmación accesibles si sustituyen `window.confirm`; preservar cancel/accept.
- Zoom/visión clínica mantiene controles de teclado del visor y alternativa de imagen si disponible.
- Contraste mínimo WCAG AA objetivo (4.5:1 texto normal; 3:1 texto grande y controles), revisar colores reales al finalizar.

La auditoría inicial encontró algunos botones icon-only con aria-label (tabla pacientes, calendario, superficies del odontograma) y navegación Bootstrap con label. El shell nuevo tiene skip link, activo de ruta, toggle con `aria-expanded`, drawer nombrado, foco inicial/trap, Escape y retorno del foco; el E2E cubre wrap de teclado en ambas direcciones. El toggle de contraseña incluye nombre y `aria-pressed`; errores de login y estados asíncronos exponen roles de anuncio. Ocho formularios asocian errores de campo con `aria-invalid`/`aria-describedby` y alertas generales donde aplican; PatientSelector anuncia resultados. Playwright comprueba orden de Tab en controles representativos y, en 29 rutas, que todo botón visible del contenido tenga texto o nombre accesible. Los controles nativos de fecha/hora se verifican por etiqueta, required y entrada de valor, ya que su secuencia interna de foco varía según navegador. Los controles de OpenSeadragon ahora tienen rol, nombre español, `tabIndex` y activación con Espacio; Playwright comprobó foco y zoom. Los colores base de texto/brand/subtle se calcularon y cumplen AA en fondos comunes; el disabled se distingue con texto legible. Aún falta revisar combinaciones de estado y medir contraste en cada módulo renderizado, además de lectores de pantalla para las pantallas restantes. No se declara conformidad WCAG global.

Pase adicional: el barrido Playwright comprueba en cada una de las 29 rutas privadas que botones, enlaces y campos visibles tengan una fuente de nombre/etiqueta (texto, label o ARIA). No se encontraron controles sin nombre en ese recorrido. Contraste calculado de los estados textuales sobre su superficie: success 6.13:1, warning 5.95:1, info 7.52:1, paciente activo 6.72:1 e inactivo 6.41:1. Estos números no sustituyen una auditoría de lector de pantalla ni cubren las etiquetas pintadas por el modelo sobre cada radiografía.

