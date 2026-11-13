# Correos con Brevo en Render Free

Render Free bloquea los puertos SMTP habituales. El backend `anymail.backends.brevo.EmailBackend` envía por HTTPS a `https://api.brevo.com/v3/smtp/email`, utilizando la API v3 de Brevo. Se conservan los mensajes HTML/texto y las plantillas de Django para invitaciones, recuperación, pacientes y recordatorios. No se configura una cola propia ni un programador de recordatorios.

## Cuenta y remitente

1. Crear una cuenta Free en https://www.brevo.com/ y completar su activación. El plan publicado incluye 300 correos al día; revisar cuotas y condiciones vigentes en https://help.brevo.com/hc/en-us/articles/208580669.
2. En la sección de remitentes, agregar y verificar la dirección que aparecerá como remitente. Autenticar el dominio si se dispone de uno. Las direcciones gratuitas como Gmail pueden ser reescritas por Brevo; verificar las condiciones del remitente en el panel.
3. En SMTP & API, pestaña API Keys, generar una clave API v3. No usar una SMTP key y no pegar la clave en chats ni versionarla.
4. Confirmar que el acceso a correo transaccional esté activado; una cuenta pendiente de revisión puede no enviar.

## Activación en Render

Agregar las siguientes variables privadas en Environment y desplegar la versión de `dev` que incluye Anymail:

```dotenv
EMAIL_PROVIDER=brevo
BREVO_API_KEY=YOUR-PRIVATE-V3-API-KEY
DEFAULT_FROM_EMAIL=SmileManager <your-verified-sender@example.com>
SMTP_TIMEOUT=15
```

No se requieren EMAIL_HOST, EMAIL_PORT, EMAIL_USER ni EMAIL_PASS para Brevo. El timeout de conexión es 5 segundos; SMTP_TIMEOUT controla el timeout de lectura HTTP. Si se selecciona Brevo sin clave o remitente explícitos, el arranque falla con un error de configuración. No activar estas variables hasta tener ambos valores; las variables privadas de despliegue no se modifican automáticamente al actualizar Git.

## Prueba real desde la computadora

Instalar requirements.txt en Python 3.13 y guardar las variables anteriores en `.env` privado. Para habilitar envío real con settings locales agregar también `DEV_EMAIL_DELIVERY=brevo`; sin esa opción el desarrollo sigue guardando correos en archivos.

```bash
python manage.py verify_email --to your-own-test-address@example.com
```

El comando envía un mensaje sintético a la dirección explícita del operador, sin datos clínicos. No ejecutarlo contra destinatarios ajenos sin autorización. La salida confirma aceptación de la API, no entrega: comprobar la bandeja y Transactional Logs de Brevo. No compartir claves, cuerpos de correo ni enlaces de recuperación al diagnosticar.

## Fallos y cuotas

Los rechazos HTTP y timeouts se propagan al flujo existente: una invitación fallida revierte su transacción; la recuperación mantiene una respuesta genérica para no revelar cuentas y registra sólo el request_id. No se reintenta automáticamente un timeout, que puede ocurrir después de que el proveedor haya aceptado el mensaje.

La aceptación por la API no demuestra entrega. Brevo puede registrar fallos posteriores o diferir correos al agotar la cuota. Esto puede hacer que enlaces de recuperación o invitación expiren antes de llegar. Revisar eventos del proveedor y solicitar un nuevo enlace cuando corresponda. La cuenta de plataforma se puede crear sin correo; crear clínicas e invitar usuarios requiere entrega configurada.

Brevo puede aplicar seguimiento de aperturas/clics a nivel de cuenta; revisar y desactivar el seguimiento para correos de autenticación. Su API no permite controlarlo por mensaje. Nunca registrar ni añadir metadatos clínicos a los eventos del proveedor.

## Verificación aislada y reversión

```bash
DJANGO_SETTINGS_MODULE=SmileManager.settings_test python manage.py test api.tests.test_brevo_email api.tests.test_email_templates api.tests.test_local_email_settings --noinput
```

Las pruebas sustituyen el transporte HTTP: verifican HTML/texto, adjuntos, rechazo, timeout, configuración y errores sin exponer secretos. No demuestran recepción real.

Para volver a SMTP seleccionar `EMAIL_PROVIDER=smtp` y configurar las credenciales SMTP en un host que permita su puerto. No hay migraciones de base de datos.

Referencias: https://anymail.dev/en/v15.2/esps/brevo/ y https://render.com/docs/free.
