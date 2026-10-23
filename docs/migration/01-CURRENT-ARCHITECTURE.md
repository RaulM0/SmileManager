# Arquitectura actual

Aplicación monolítica Django 5.2.8. Las function views mezclan HTTP, validación, consultas, reglas y efectos secundarios; las plantillas contienen Bootstrap, CSS propio y JavaScript inline. PostgreSQL se usa localmente mediante Docker; producción usa `DATABASE_URL`, S3, WhiteNoise, Gmail SMTP y Gunicorn.

## Flujo actual

`Navegador → LoginRequiredMiddleware → URL → function view → ORM/Form/servicio externo → Template/JsonResponse/archivo`.

## Aplicaciones

| App            | Responsabilidad                                                                                       |
| -------------- | ----------------------------------------------------------------------------------------------------- |
| Home           | panel y aviso de privacidad                                                                           |
| Sesiones       | login/logout con sesión Django                                                                        |
| Usuarios       | perfil uno-a-uno creado por señal                                                                     |
| Pacientes      | pacientes, expediente, consultas, imágenes, email, odontograma, estudios, consentimiento, Excel y PDF |
| Citas          | agenda y recordatorios por management command                                                         |
| DiagnosticosIA | listado y análisis síncrono con YOLO/PyTorch                                                          |

No existen DRF, serializers, services, managers personalizados, Celery, WebSockets, cache, fixtures, seeds ni CI. Los tests legacy son archivos vacíos. La autorización real consiste en filtrar todos los objetos por `request.user`/`paciente__medico`; el middleware exige autenticación para todo salvo login, logout, admin y static.

## Integraciones y efectos

- S3 mediante `django-storages` en producción; filesystem local en desarrollo.
- SMTP Gmail para contacto y recordatorios; consola en desarrollo.
- YOLO carga `train_model/best.pt` al importar la vista y procesa sin cola.
- Pandas/openpyxl produce tres Excel.
- xhtml2pdf produce el estudio comparativo.
- Bootstrap, Bootstrap Icons, OpenSeadragon, Google Fonts y Select2/jQuery se consumen por CDN.
