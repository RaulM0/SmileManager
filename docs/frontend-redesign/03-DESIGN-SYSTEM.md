# Design system — Clinical Operations Workspace

## Principios

Superficie clínica sobria, densa, legible y enfocada en tareas. La identidad procede de navegación, jerarquía y controles del dominio. No se agregan métricas ni módulos sin datos.

## Tokens

| Token | Valor / regla |
|---|---|
| Font | Inter si está disponible; fallback `Inter, ui-sans-serif, system-ui, sans-serif`; sin descarga externa forzada. |
| Escala | 12/14/16 px UI, 20 px sección, 23–24 px página; cifras/tablas con números tabulares. |
| Fondo | `#f4f6f7` workspace; `#ffffff` surface; `#f8fafb` subtle. |
| Texto | `#1d2a32` primary; `#52616a` secondary; `#626f76` subtle/muted (AA en superficie y canvas). |
| Marca | teal clínico `#176b78`; hover `#105763`; tinte `#e8f3f4`. |
| Semánticos | success `#236b4c`; warning `#8a5a0a`; danger `#a13c38`; info `#315f91`; neutral `#56636c`. Siempre etiqueta visible. |
| Espaciado | base 4 px; controles 8/12; secciones 16/24; gutters 14–16 mobile, 24 tablet, 28 desktop. |
| Radio | 4 px controles, 5–6 px paneles; pills solo estados compactos. |
| Bordes | 1 px `#dce3e6`; separación sin sombra como valor inicial. |
| Sombra | ninguna en tablas/paneles; sombra baja solo en overlays. |
| Focus | outline 2 px `#176b78`, offset 2 px. |
| Tabla | filas 44 px estándar; 36 px compacta; encabezado 11 px; horizontal scroll local. |
| Formulario | controles 39–40 px; label 13 px semibold; errores junto al campo. |

## Contraste calculado

Contraste WCAG relativo para textos principales: tinta `#1d2a32` sobre blanco 14.69:1; secondary `#52616a` sobre blanco 6.41:1; subtle `#626f76` sobre canvas `#f4f6f7` 4.78:1 y sobre blanco 5.18:1; marca `#176b78` sobre blanco 6.16:1. El muted de Bootstrap se sobrescribe con el token subtle. Los controles disabled usan texto `#52616a` sobre `#e8edef` (5.43:1) y conservan su estado semántico disabled.

Estas mediciones cubren la paleta de texto/base; no sustituyen la revisión de combinaciones de estados, contenido dinámico ni todos los componentes renderizados.

## Estados clínicos

Citas: Pendiente → warning; Completada → success; Cancelada → neutral. Waiting/In progress/No-show/Confirmed solo se mapean si llegan de API. Los seis estados dentales conservan su semántica y leyenda actual. Nunca se comunica estado solo mediante color.

## Tailwind y CSS de producto

Tailwind CSS 3.4.17 y PostCSS están instalados sin actualizar React/Vite. `tailwind.config.cjs` escanea React, define tokens, utiliza prefijo `co-` y desactiva preflight. `postcss.config.cjs` compila Tailwind. El shell y componentes compartidos usan utilidades y `@apply` Tailwind. Bootstrap CSS/JS y su dependencia se retiraron tras migrar las clases visuales; el antiguo collapse de navbar se reemplazó por drawer React con estado accesible. `bootstrap-icons` continúa como iconografía única. El build confirma que Tailwind compila y detecta clases; CSS de producción 127.65 kB.

Los formularios compartidos de paciente y cita iniciaron el primer slice de migración: componentes `clinical-form-*` declarados en `@layer components` con utilidades Tailwind `co-*`; conservan etiquetas, restricciones y validaciones. Controles mantienen altura mínima de 39px, tipografía compacta, borde fino, foco global visible, error asociado y botón primario con disabled explícito.

