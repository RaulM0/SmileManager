# Registro de decisiones

### DEC-001 — Autenticación por sesión Django

Contexto: el legacy usa `django.contrib.auth`, cookies y CSRF; React se servirá en el mismo origen.

Opciones: JWT, token persistente, sesión Django.

Decisión: conservar sesión Django y CSRF. Login/logout serán endpoints DRF; React enviará `credentials: include` y `X-CSRFToken`.

Razón: preserva sesiones, permisos y operación del admin, reduce superficie de cambio y evita introducir almacenamiento de tokens.

Impacto: frontend y API deben compartir origen o configurar explícitamente CORS/CSRF. Archivos: settings, API auth, cliente HTTP React.

### DEC-002 — Convivencia incremental

Contexto: se exige paridad estricta y el legacy es la única especificación ejecutable.

Decisión: Django permanece en raíz; API bajo `/api/v1/`; React en `frontend/` y se monta inicialmente en `/app/`. No se mueven modelos ni migraciones.

Razón: permite comparación funcional y rollback por ruta.

Impacto: dos interfaces convivirán hasta validación final.

### DEC-003 — Servicios para reglas compartidas

Decisión: reglas con mutaciones/efectos se extraen a módulos `services.py`; serializers validan entrada y views manejan HTTP. Querysets propietarios se centralizan cuando aporten seguridad.

Razón: evita duplicar lógica entre legacy y API y facilita tests.

### DEC-004 — Stack frontend

Contexto: no existía toolchain JavaScript.

Decisión: React 19, Vite 8, React Router, Bootstrap 5 y Bootstrap Icons. En desarrollo Vite hace proxy de `/api` y `/media` a Django.

Razón: conserva el sistema visual Bootstrap, mantiene cookies same-origin desde la perspectiva del navegador y permite build/test/lint rápidos.

Impacto: `frontend/` contiene package lock reproducible; producción deberá servir `dist` bajo `/app/` o mediante hosting del mismo origen.

### DEC-005 — Build React servido por Django

Contexto: sesión y CSRF se conservan same-origin y se necesita convivencia con el legacy.

Decisión: Vite genera assets con base `/static/react/`; Django sirve `index.html` para `/app/` y cualquier ruta profunda de React. `BrowserRouter` usa basename `/app` en producción.

Razón: evita CORS, conserva las cookies seguras y permite desplegar ambos frontends de forma incremental.

Impacto: después de cada build debe reiniciarse el proceso de desarrollo Django si su finder de estáticos conservó el nombre hash anterior.

### DEC-006 — Renovación CSRF después del login

Contexto: Django rota el token CSRF al ejecutar `login()`. Conservar el token previo permitió autenticar, pero las mutaciones posteriores devolvían 403.

Decisión: `POST /api/v1/auth/login/` devuelve el nuevo `csrf_token` y `AuthContext` reemplaza inmediatamente el token del cliente.

Razón: es el comportamiento seguro nativo de Django y mantiene sesión/cookies sin introducir JWT.

Impacto: el contrato de login incluye `authenticated`, `user` y `csrf_token`; existe prueba backend y E2E de regresión.

### DEC-007 — E2E reproducible y aislado

Contexto: ejecutar Playwright contra la base local ensuciaba pacientes, citas y media reales.

Decisión: `settings_e2e` usa SQLite y media dedicados; setup/teardown recrean y eliminan ambos, preparan el usuario y Playwright administra el servidor Django.

Razón: la validación completa puede repetirse con un comando sin tocar PostgreSQL ni archivos clínicos del usuario.

Impacto: `npm run test:e2e` requiere el entorno Python instalado y el modelo `train_model/best.pt`, pero no requiere preparar datos manualmente.

### DEC-008 — Integraciones de despliegue

Contexto: SMTP y S3 dependen de credenciales y disponibilidad externas distintas por entorno.

Decisión: verificar funcionalidad con backends Django intercambiables y aislados; considerar la comprobación de credenciales reales un smoke test operativo de cada despliegue.

Razón: prueba contratos, contenido, uploads y efectos sin almacenar secretos ni hacer envíos reales durante CI.

Impacto: la migración funcional no depende de una cuenta externa concreta; despliegue debe comprobar conectividad con sus propios secretos.
