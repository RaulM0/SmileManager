# Recuperación de contraseña

## Arquitectura y alcance

El sistema usa `django.contrib.auth.User`; el login utiliza `username`. `email` no es único. Se requiere exactamente una cuenta coincidente, sin distinguir mayúsculas, que esté activa y tenga contraseña utilizable. Si el correo está duplicado, vacío, pertenece a una cuenta inactiva o la cuenta no tiene contraseña utilizable, no se envía enlace. Las respuestas de solicitud válidas son iguales. La resolución de correos duplicados requiere intervención administrativa fuera de este flujo; **BUSINESS DECISION REQUIRED**.

`POST /api/v1/auth/password-reset/request/` recibe `email`. `POST /api/v1/auth/password-reset/confirm/` recibe `uid`, `token`, `new_password`, `confirm_password`. Son públicos, aceptan JSON y no autentican por cookies; aplican la comprobación de origen existente. Sin autenticación de sesión no dependen de CSRF de sesión. No existe endpoint GET que modifique datos; la validez del enlace se comprueba al enviar el formulario.

Django `PasswordResetTokenGenerator` y `uidb64` vinculan el token a la cuenta y a su estado de contraseña. `PASSWORD_RESET_TIMEOUT` se configura en segundos, por defecto 1800. Cambiar la contraseña invalida los enlaces anteriores; el bloqueo de fila y la transacción impiden que dos confirmaciones concurrentes triunfen. No se guarda el token en base de datos. No se prometen enlaces distintos si se solicitan en el mismo segundo.

El enlace usa `FRONTEND_URL` configurada en servidor y el fragmento `#uid=...&token=...`: el fragmento no llega a las rutas HTTP del servidor o proxy. El navegador elimina el fragmento de la barra al iniciar la página, por lo que recargar esa página requiere volver a abrir el enlace original. Un fragmento no protege frente a código malicioso en el navegador, extensiones, correo comprometido o captura de pantalla. No se aceptan `next` ni destinos aportados por la solicitud.

## Contraseña, sesiones y auditoría

Se aplican `AUTH_PASSWORD_VALIDATORS` de Django, se usa `set_password()` y se mantienen `is_active`, grupos y permisos. Confirmar en un usuario inactivo falla. Se bloquea al usuario y se ponen en blacklist sus refresh no expirados en la misma transacción que el cambio y `PASSWORD_RESET_COMPLETED`. El evento identifica el recurso de usuario, pero el actor es nulo: poseer el enlace no demuestra quién es la persona. `PASSWORD_RESET_REQUESTED` no guarda email ni usuario. No se registra password, token, JWT ni enlace en AuditEvent.

La etapa 2 vincula access y refresh a `AuthSession`. Recuperar contraseña revoca esas sesiones, por lo que los access anteriores fallan en su siguiente validación aunque no haya vencido su JWT. Refresh y session comprueban contraseña y sesión bajo bloqueo de usuario; login vuelve a comprobar la contraseña después de adquirir ese bloqueo. Los tokens previos sin identificador de sesión se rechazan: el despliegue requiere nuevo inicio de sesión. Recuperar contraseña no elimina MFA. Ver [controles y transición](etapa-2-resultados.md).

## Antienumeración y abuso

El mismo mensaje/status/cuerpo se devuelve para correo válido existente, inexistente, duplicado, inactivo o no recuperable; formato inválido recibe 400 independientemente de existencia. La entrega SMTP se realiza de forma síncrona solo para cuentas elegibles: **puede haber diferencias de tiempo observables**. La igualdad temporal no está garantizada; cola durable y reducción de fuga temporal deben evaluarse antes de producción. No se registran direcciones ni excepciones SMTP completas en logs de aplicación.

Throttle inicial revisable: `THROTTLE_PASSWORD_RESET_IP=10/hour`, `THROTTLE_PASSWORD_RESET_ACCOUNT=3/hour`, `THROTTLE_PASSWORD_RESET_CONFIRM=20/hour`. El identificador por correo usa HMAC, se aplica también a correos inexistentes y puede permitir bloqueo dirigido temporal. Producción exige Redis con ventanas atómicas compartidas; fallos del servicio impiden continuar la operación protegida. Las cabeceras reenviadas solo se usan desde proxies explícitamente confiables. Desarrollo/pruebas sin Redis conservan limitación local. Ver [configuración y límites](rate-limiting.md). Se requieren además protección perimetral y validación de topología real.

## Configuración y operación

- `FRONTEND_URL`: URL base confiable del frontend, incluyendo `/app` si aplica; HTTPS obligatorio en producción. Sin configurar no se envía correo y la API mantiene respuesta genérica.
- `DEFAULT_FROM_EMAIL`: remitente configurado en servidor. SMTP usa `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_USER`, `EMAIL_PASS` y `SMTP_TIMEOUT`; no guardar sus valores secretos en Git.
- `PASSWORD_RESET_TIMEOUT`: segundos; configuración positiva, por defecto 1800.
- Variables de throttling indicadas arriba. Nunca poner secretos en variables frontend.

En desarrollo `settings_local` usa por defecto backend de archivos en `.local-mail/` o `DEV_EMAIL_DIR`; requiere `FRONTEND_URL` configurada. Son mensajes con enlaces de acceso: restringir acceso al directorio y eliminarlos según política local. El directorio por defecto está ignorado por Git. Tests usan correo en memoria; E2E usa archivos en directorio temporal único que elimina su propio teardown. No se envían emails reales durante pruebas.

Para probar entrega real desde desarrollo, configurar explícitamente `DEV_EMAIL_DELIVERY=smtp` en el entorno del proceso Django, junto con `FRONTEND_URL`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_USER`, `EMAIL_PASS` y `DEFAULT_FROM_EMAIL` según el proveedor. Reiniciar Django después de establecerlos. Los valores y credenciales deben mantenerse fuera del repositorio; no enviar credenciales por chat. El modo `smtp` realiza entregas reales y no verifica que el proveedor, remitente o dominio estén autorizados. Cualquier otro valor de `DEV_EMAIL_DELIVERY` falla al iniciar. `settings_test` y `settings_e2e` conservan backends aislados aunque se configure el modo local SMTP.

## Antes de producción

**INFRASTRUCTURE VERIFICATION REQUIRED:** SMTP/proveedor, entrega real, remitente, SPF/DKIM/DMARC, TLS/HTTPS, `FRONTEND_URL`, secretos, rate limiting distribuido/perimetral, proxy/IP, alertas de abuso, monitorización de fallos de entrega y retención de logs. Los tiempos de respuesta SMTP pueden permitir inferencia de existencia. Corregir duplicados de email mediante proceso autorizado. El audit log comparte DB y no es WORM. No se afirma preparación de producción por las pruebas.
