# Retiro de interfaces HTML heredadas

Las antiguas interfaces Django bajo `/sesiones/`, `/home/`, `/registroPacientes/`, `/menu_citas/`, `/diagnosticos/` y `/admin/` fueron retiradas y responden 404. La raíz redirige a `/app/`; React sirve las pantallas y `/api/v1/` publica los contratos DRF. Los consumidores de enlaces históricos deben actualizarse.

Se conservan las plantillas internas de correo y de PDF, que usa la API para generar documentos y mensajes; no son pantallas web. También se conserva la API DRF de compatibilidad para datos sin clínica durante la migración controlada. Retirar la interfaz HTML no asigna datos históricos ni completa por sí solo el aislamiento multitenant.

Las pruebas `api.tests.test_retired_html_routes` verifican las rutas retiradas incluso con sesión de superusuario, y las pruebas de API comprueban acceso y descarga protegida de archivos.
