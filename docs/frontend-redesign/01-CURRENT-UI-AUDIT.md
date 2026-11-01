# Auditoría de UI actual

## Estado y alcance

Inspección inicial de `frontend/src`, rutas en `App.jsx`, dependencias, cliente API, auth, layout, estilos globales, componentes compartidos, páginas, tests unitarios y E2E. Aplicación React 19 + React Router 7 + Vite 8. Bootstrap 5.3.8 y Bootstrap Icons 1.13.1 están cargados globalmente; no hay configuración Tailwind identificada. CSS propio está en `src/styles/app.css`, con tokens dentales simples, navbar degradada y reglas específicas para login, odontograma e imágenes.

## Navegación y rutas actuales

- `/login` pública; rutas de negocio bajo `ProtectedRoute` y `AppLayout`.
- Inicio `/`; privacidad `/privacy`.
- Pacientes `/patients`, `/patients/list`, `/patients/search`, `/patients/new`, `/patients/contact`, `/patients/:id`, `/patients/:id/edit`.
- Expediente `/clinical-record`, `/patients/:id/record`, `medical-history`, `consultations/new`, `consultations`, `consultations/:id/prescription`, `images`, `images/upload`, `images/search`, `images/history`, `odontogram`, `comparative-study`, `consent`.
- Citas `/appointments`, `/appointments/new`, `/appointments/:id`, `/appointments/:id/edit`.
- Diagnósticos `/diagnostics`, `/diagnostics/:id`; exportaciones `/exports`.
- `*` redirige a `/`. No se deben eliminar rutas aunque no estén en la navbar.

La navbar enlaza solo Inicio, Citas, Pacientes y Diagnósticos; las otras páginas se alcanzan desde flujos/contexto. El usuario actual y logout aparecen en topbar; aviso de privacidad en footer. No se observó filtrado de rutas o acciones por rol en el frontend revisado. `ProtectedRoute` exige sesión y conserva destino en `location.state.from` para volver tras autenticación.

## Datos, requests y estados

`api()` hace `fetch` a `/api/v1/`, incluye credenciales, serializa JSON salvo FormData, adjunta CSRF en métodos mutantes y lanza error con `status` y `payload`. `AuthProvider` carga sesión, login/logout y CSRF. Algunas pantallas presentan loading/error explícitos; otras dejan rechazo de promesa sin UI de error (ver inventario y regresión pendiente). No alterar payloads ni endpoints.

## Flujos de dominio observados

- Inicio consulta `dashboard/`, recibe conteo de pacientes y listas `today`/`upcoming`; permite ir a citas/pacientes.
- Agenda contiene calendario mensual local, lista, búsqueda/status en query string y acciones POST `complete`/`cancel`.
- Pacientes: selector/autocomplete, listado con `search` y `page`, CRUD, activación/desactivación, contacto por correo; formularios compartidos validan localmente.
- Expediente: antecedentes médicos, consulta y receta imprimible, historial, odontograma FDI permanente/decidua y cinco superficies por diente, imágenes, estudio comparativo y PDF, consentimiento con identificación.
- Imágenes: filtros por fecha/consulta, upload multipart, descarga y eliminación confirmada.
- Diagnóstico IA: filtro paciente/tipo/fecha; analiza imagen, muestra resultados/imagen con OpenSeadragon.
- Exportación descarga tres XLSX. Aviso de privacidad es contenido estático.

## Riesgos y oportunidades

- Layout actual es una navbar horizontal y footer, no workspace; enlaces secundarios no evidencian contexto activo.
- Bootstrap da consistencia básica pero cards/sombras se repiten y no hay tokens de densidad ni semanticidad clínica centralizados.
- Navegación móvil depende del plugin Collapse de Bootstrap; tests E2E comprueban el menú.
- Agenda es vista mensual + tabla, no existe vista por profesional/recurso ni selector de semana. No inventar capacidad: `DATA_REQUIREMENT` para profesional/recurso y semana si la API no los devuelve.
- Paciente no tiene Patient 360 compuesto; el record es un menú de enlaces. Se puede mejorar contexto con los datos existentes, preservando rutas.
- No se observan módulos de pagos, tratamientos o inventario en las rutas actuales; no agregarlos por diseño.
- Cambios preexistentes en Git incluyen configuraciones/backend, numerosos `.pyc`, `compose.yaml`, `manage.py`, `SmileManager/settings_local.py` y `frontend/package-lock.json`. Respetar; no revertir ni atribuirlos a este trabajo.

## Cobertura de análisis

La lista completa de archivos, APIs y controles está en `02-FUNCTIONAL-UI-INVENTORY.md`. El análisis de código no equivale a validación visual/runtime; ejecutar tests/build y, si backend está disponible, E2E antes de marcar verificado.

