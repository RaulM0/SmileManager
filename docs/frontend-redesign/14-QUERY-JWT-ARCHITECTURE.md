# Arquitectura de datos y autenticación JWT

## Contrato vigente antes de esta fase

- React consultaba `api/v1/auth/session/` para CSRF y enviaba `X-CSRFToken` con cookie de sesión.
- Las páginas Django bajo `/sesiones/` usan sesión de Django y permanecen disponibles; no son parte de la SPA.
- GET y mutaciones vivían en páginas, con un hook de GET sin caché compartida.
- Las descargas XLSX y PDF de la SPA eran enlaces directos a la API.

## Objetivo de implementación

- API React protegida por JWT Bearer; access de cinco minutos solo en memoria, refresh de ocho horas en cookie HttpOnly, Secure en producción, SameSite Strict y restringida a `/api/v1/auth/`.
- `/auth/session/` restaura un access desde el refresh tras recargar; `/auth/refresh/` rota y revoca el refresh; `/auth/logout/` revoca el refresh y elimina la cookie. Rutas clínicas comprueban propietario como antes. Las sesiones Django tradicionales quedan separadas de la API.
- El cliente reintenta una sola vez tras 401 y comparte una renovación en curso. Logout y cambio de identidad vacían access y caché. La API devuelve `Cache-Control: no-store` en respuestas de sesión.
- TanStack Query usa claves por recurso/ID/filtro, caché de memoria con tiempo de frescura explícito, sin persistencia clínica en localStorage y con invalidación de claves afectadas tras mutaciones. Los errores 400 mantienen su asociación al campo; los resultados transitorios siguen en toast.
- Los XLSX y PDF de la API se descargan como Blob mediante Bearer para conservar su acción visible.

## Riesgos de paridad que se prueban

- Recarga de SPA, expiración y refresh único, credenciales erróneas, logout y segunda cuenta sin datos de la primera.
- Alta/edición/desactivación de paciente; alta/edición/cancelación/completado de cita; clínica, odontograma, imágenes, análisis, correo y descargas.
- No reutilizar datos clínicos entre identidades y no usar caché persistente.

## Implementación

- `api/client.ts` guarda access solo en memoria, añade Bearer a las peticiones y renueva una sola vez al recibir 401; una renovación simultánea se comparte. Las pruebas unitarias cubren cabecera y renovación concurrente.
- `AuthContext` restaura sesión desde refresh HttpOnly, limpia access y caché al cambiar de identidad, y rechaza datos de la cuenta anterior.
- `query/keys.ts` y `query/latestCachedData.ts` definen identidad por recurso, paciente y filtros; las listas conservan la última respuesta correcta ante un error de filtro.
- `useResource` comparte GET de detalle e historial. Listas de pacientes, citas, diagnósticos e imágenes, y el selector de pacientes, usan TanStack Query. Las mutaciones principales invalidan sus listas relacionadas.
- Los medios y descargas clínicas protegidos se solicitan con Bearer; el backend comprueba propiedad antes de responder.
- Django mantiene `/sesiones/` para sus páginas tradicionales; DRF solo acepta JWT para la API de la SPA.
- `SECRET_KEY` debe existir en el entorno de producción; el arranque falla si falta. La instalación requiere migrar `token_blacklist` con `python manage.py migrate` antes de recibir tráfico. Local y E2E mantienen su configuración de desarrollo.

## Validación actual

`api.tests`: 42/42 (incluye origen de refresh y acceso propietario a imagen); `npm run lint`, `npm run typecheck`, `npm test` (8/8), `npm run build` y Playwright E2E (3/3): PASS. El E2E detectó una regresión de última lista válida ante 503; se corrigió mediante el caché de respuestas exitosas y se confirmó en el flujo clínico completo.

## Límite de seguridad conocido

Los serializers de compatibilidad aún devuelven URL de almacenamiento para archivos clínicos y las rutas legacy Django pueden enlazarlas. La SPA usa rutas API autenticadas y con comprobación de propietario, pero la privacidad de los archivos depende también de que el servidor de medios de producción no publique el directorio directamente. Esa infraestructura debe revisarse antes de declarar protección integral de archivos. No se cambió el contrato de respuesta de esos serializers para preservar clientes existentes.
