# Rediseño del frontend SmileManager

## Propósito

Memoria de auditoría e implementación del espacio operativo clínico. La paridad funcional es el criterio principal: rutas, requests, campos, parámetros, permisos, confirmaciones, uploads, downloads y flujos existentes se conservan.

## Alcance conocido

Frontend SPA en `frontend/`: React 19, React Router 7, Vite 8, Bootstrap 5.3.8 y Bootstrap Icons 1.13.1. Tailwind CSS 3.4.17/PostCSS se incorporaron después de la auditoría, con preflight desactivado y prefijo `co-` para convivir durante la migración. El backend/API no forma parte de este rediseño.

## Orden de lectura

1. `01-CURRENT-UI-AUDIT.md` — arquitectura y superficie actual.
2. `02-FUNCTIONAL-UI-INVENTORY.md` — contrato funcional UI-XXX.
3. `03-DESIGN-SYSTEM.md` y `04-UX-PATTERNS.md` — dirección y patrones.
4. `05-COMPONENT-MAPPING.md`, `06-SCREEN-MIGRATION.md` — destino e implementación.
5. `07-RESPONSIVE-STRATEGY.md`, `08-ACCESSIBILITY.md`.
6. `09-REDESIGN-STATUS.md`, `10-REGRESSION-CHECKLIST.md`.
7. `11-DESIGN-DECISIONS.md`, `12-FINAL-VALIDATION.md`.

## Convenciones

- `ANALYZED`: revisado en el código; no implica que ya haya sido probado en runtime.
- `REDESIGNED`: cambio de presentación implementado.
- `VERIFIED`: comprobado con ejecución relevante. No se usa por inferencia.
- `DATA_REQUIREMENT`: posibilidad UX que necesita datos/API hoy no disponibles; no se simulan datos.

## Estado actual (24-10-2026)

Inventario UI-001–UI-034 y matriz de rutas preparados. Tailwind 3.4.17 compila con prefijo `co-`; Bootstrap CSS/JS y su dependencia ya se retiraron, mientras `bootstrap-icons` permanece. Shell, Inicio, Patient 360, formularios de paciente/cita, expediente, odontograma, imágenes, estudio comparativo, consentimiento, diagnósticos, exportaciones, login y privacidad recibieron cambios de presentación. Lint, unit, build y E2E (3/3, salida 0) pasan tras retirar Bootstrap; E2E comprueba overflow en rutas clave a 390/768 px y el foco/ciclo de teclado del drawer móvil. Se midió la paleta base y se mejoró el contraste muted. Capturas desktop/tablet/mobile y drawer inspeccionadas; falta revisión manual general de rutas y estados. Ver `09-REDESIGN-STATUS.md` y `12-FINAL-VALIDATION.md`.
