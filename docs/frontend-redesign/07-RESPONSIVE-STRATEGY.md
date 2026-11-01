# Estrategia responsive

En Inicio, la tabla de próximas citas mantiene todas sus columnas en un contenedor desplazable horizontalmente en móvil; se muestra una indicación visible de gesto en <576px, oculta en tablet/desktop. Playwright comprueba la indicación, que no aparezca a 768px y que no cause overflow del documento. Las columnas siguen presentes para no perder datos ni acciones.

- Desktop (≥1200): sidebar persistente de ancho contenido; workspace fluido; tablas mantienen columnas y densidad. Agenda conserva grilla mensual.
- Laptop (992–1199): sidebar compacto o colapsable; evitar que controles del calendario compriman celdas.
- Tablet (768–991): navegación drawer accionable por botón con aria-expanded; filtros en filas compactas; tablas con overflow identificado.
- Mobile (<768): navegación drawer; page header apilado; acciones frecuentes visibles; tabla con overflow local etiquetado o composición por registro conservando todas las acciones; formulario una columna; master/detail por navegación de ruta.
- Odontograma: cuadrantes nombrados en dos columnas desktop/tablet y una columna bajo 576 px; cada fila de piezas conserva scroll horizontal propio, anunciado en texto. Superficies de 24×24 px; resumen de cinco valores en dos columnas móvil. Playwright comprueba scroll local, dimensiones táctiles, layout y ausencia de overflow de documento.
- Viewer clínico: paneles original/analizada lado a lado en desktop, apilados bajo 992 px; visor de 420 px desktop y 310 px móvil, toolbar visible y sin overflow de documento. Playwright comprueba ambos viewers y PNG locales con la radiografía de 612×323 px del repositorio; la tabla de detecciones conserva scroll horizontal móvil con aviso visible. Capturas 1280/390 inspeccionadas, incluida vista ampliada mediante teclado.
- Preferencia `prefers-reduced-motion`; sin animación decorativa.

La agenda de citas utiliza una cuadrícula mensual de 42 días en desktop. Bajo 768 px presenta primero una agenda de las citas del mes visible, agrupada por fecha y ordenada por hora; el selector Agenda/Mes permite abrir la misma cuadrícula mensual con scroll horizontal local. Las flechas de mes y Hoy gobiernan ambas vistas, y los filtros `status/search` existentes se aplican a las dos. La tabla de acciones permanece disponible bajo el calendario, con scroll local en móvil. Playwright comprueba el selector, las indicaciones de scroll y el ancho de documento a 390 px; las capturas desktop/móvil se inspeccionaron.

Implementados: shell drawer bajo 992 px, header/acciones adaptables, nav clínica con scroll horizontal, tablas con overflow local, formularios en una columna y cuadrantes FDI reflow. Inspección visual con Chromium: dashboard desktop/tablet/mobile; Patient 360, detalle de paciente, hubs de paciente/expediente/imágenes, selector clínico, detalle de cita, agenda, odontograma y diagnóstico en desktop/móvil; drawer móvil. Playwright recorre las 29 rutas privadas existentes con h1 visible y sin overflow del documento a 1280/768/390 px; también verifica drawer, CTA y foco de teclado. Sigue pendiente una revisión visual humana de cada estado y combinación de datos en tablet/móvil.

