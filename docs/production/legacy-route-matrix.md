# Matriz estática de rutas HTML

Generada con `python scripts/inventory_legacy_routes.py`; es inventario estático, no prueba de comportamiento. Middleware de sesión y CSRF aplican según configuración; cada celda marcada revisar requiere prueba. Consumidor externo desconocido.

| Ruta | Métodos | Auth | CSRF | Ownership | Write | Servicio | Audit | Versión | Archivos | Consumidor | Estado |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `/home/` | GET/POST u otros: revisar | middleware* | middleware* | scoped/owned* | No detectada* | revisar/NA | revisar/NA | revisar/NA | no detectado* | desconocido | BLOCKED |
| `/home/aviso-privacidad/` | GET/POST u otros: revisar | middleware* | middleware* | revisar/NA | No detectada* | revisar/NA | revisar/NA | revisar/NA | no detectado* | desconocido | BLOCKED |
| `/sesiones/login/` | GET/POST u otros: revisar | middleware* | middleware* | revisar/NA | No detectada* | revisar/NA | revisar/NA | revisar/NA | no detectado* | desconocido | BLOCKED |
| `/sesiones/logout/` | POST | middleware* | middleware* | revisar/NA | No detectada* | revisar/NA | revisar/NA | revisar/NA | no detectado* | desconocido | BLOCKED |
| `/registroPacientes/archivos/<str:kind>/<int:resource_id>/<str:field>/` | GET | middleware* | middleware* | scoped/owned* | No detectada* | revisar/NA | mapeado* | revisar/NA | revisar* | desconocido | BLOCKED |
| `/registroPacientes/` | GET/POST u otros: revisar | middleware* | middleware* | revisar/NA | No detectada* | revisar/NA | revisar/NA | revisar/NA | no detectado* | desconocido | BLOCKED |
| `/registroPacientes/registrar_pacientes/` | GET/POST u otros: revisar | middleware* | middleware* | revisar/NA | POST: revisar | Sí* | mapeado* | revisar/NA | no detectado* | desconocido | BLOCKED |
| `/registroPacientes/todosPacientes` | GET/POST u otros: revisar | middleware* | middleware* | scoped/owned* | No detectada* | revisar/NA | revisar/NA | revisar/NA | no detectado* | desconocido | BLOCKED |
| `/registroPacientes/buscar_pacientes/` | GET/POST u otros: revisar | middleware* | middleware* | scoped/owned* | No detectada* | revisar/NA | revisar/NA | revisar/NA | no detectado* | desconocido | BLOCKED |
| `/registroPacientes/ver_paciente/<int:id>/` | GET/POST u otros: revisar | middleware* | middleware* | scoped/owned* | No detectada* | revisar/NA | mapeado* | revisar/NA | no detectado* | desconocido | BLOCKED |
| `/registroPacientes/editar_paciente/<int:id>/` | GET/POST u otros: revisar | middleware* | middleware* | scoped/owned* | POST: revisar | Sí* | mapeado* | revisar/NA | no detectado* | desconocido | BLOCKED |
| `/registroPacientes/eliminar_paciente/<int:id>/` | GET/POST u otros: revisar | middleware* | middleware* | scoped/owned* | No detectada* | Sí* | mapeado* | revisar/NA | no detectado* | desconocido | BLOCKED |
| `/registroPacientes/menu_historial/` | GET/POST u otros: revisar | middleware* | middleware* | scoped/owned* | No detectada* | revisar/NA | revisar/NA | revisar/NA | no detectado* | desconocido | BLOCKED |
| `/registroPacientes/buscar_pacientes_ajax/` | GET/POST u otros: revisar | middleware* | middleware* | scoped/owned* | No detectada* | revisar/NA | revisar/NA | revisar/NA | no detectado* | desconocido | BLOCKED |
| `/registroPacientes/antecedentes/<int:id>/` | GET/POST u otros: revisar | middleware* | middleware* | scoped/owned* | POST: revisar | Sí* | mapeado* | save_record* | no detectado* | desconocido | BLOCKED |
| `/registroPacientes/consultas/<int:id>/` | GET/POST u otros: revisar | middleware* | middleware* | scoped/owned* | POST: revisar | revisar/NA | revisar/NA | revisar/NA | no detectado* | desconocido | BLOCKED |
| `/registroPacientes/receta/<int:id>/` | GET/POST u otros: revisar | middleware* | middleware* | scoped/owned* | No detectada* | revisar/NA | revisar/NA | revisar/NA | no detectado* | desconocido | BLOCKED |
| `/registroPacientes/historial_consultas/<int:id>/` | GET/POST u otros: revisar | middleware* | middleware* | scoped/owned* | No detectada* | revisar/NA | revisar/NA | revisar/NA | no detectado* | desconocido | BLOCKED |
| `/registroPacientes/imagenes_clinicas/<int:id>/` | GET/POST u otros: revisar | middleware* | middleware* | scoped/owned* | No detectada* | revisar/NA | revisar/NA | revisar/NA | revisar* | desconocido | BLOCKED |
| `/registroPacientes/cargar_imagen/<int:id>/` | GET/POST u otros: revisar | middleware* | middleware* | scoped/owned* | POST: revisar | revisar/NA | mapeado* | revisar/NA | revisar* | desconocido | BLOCKED |
| `/registroPacientes/buscar_imagen/<int:id>/` | GET/POST u otros: revisar | middleware* | middleware* | scoped/owned* | No detectada* | revisar/NA | revisar/NA | revisar/NA | revisar* | desconocido | BLOCKED |
| `/registroPacientes/eliminar_imagen/<int:imagen_id>/` | POST | middleware* | middleware* | scoped/owned* | POST: revisar | revisar/NA | mapeado* | revisar/NA | revisar* | desconocido | BLOCKED |
| `/registroPacientes/historial_imagenes/<int:id>/` | GET/POST u otros: revisar | middleware* | middleware* | scoped/owned* | No detectada* | revisar/NA | revisar/NA | revisar/NA | revisar* | desconocido | BLOCKED |
| `/registroPacientes/exportar_datos/` | GET/POST u otros: revisar | middleware* | middleware* | revisar/NA | No detectada* | revisar/NA | revisar/NA | revisar/NA | no detectado* | desconocido | BLOCKED |
| `/registroPacientes/exportar_pacientes/` | GET/POST u otros: revisar | middleware* | middleware* | revisar/NA | No detectada* | revisar/NA | mapeado* | revisar/NA | no detectado* | desconocido | BLOCKED |
| `/registroPacientes/exportar_consultas/` | GET/POST u otros: revisar | middleware* | middleware* | revisar/NA | No detectada* | revisar/NA | mapeado* | revisar/NA | no detectado* | desconocido | BLOCKED |
| `/registroPacientes/exportar_imagenes/` | GET/POST u otros: revisar | middleware* | middleware* | revisar/NA | No detectada* | revisar/NA | mapeado* | revisar/NA | revisar* | desconocido | BLOCKED |
| `/registroPacientes/contactar_pacientes/` | GET/POST u otros: revisar | middleware* | middleware* | scoped/owned* | No detectada* | revisar/NA | revisar/NA | revisar/NA | no detectado* | desconocido | BLOCKED |
| `/registroPacientes/contacto/<int:id>/` | GET/POST u otros: revisar | middleware* | middleware* | scoped/owned* | No detectada* | revisar/NA | revisar/NA | revisar/NA | no detectado* | desconocido | BLOCKED |
| `/registroPacientes/enviar_mensaje/` | GET/POST u otros: revisar | middleware* | middleware* | scoped/owned* | No detectada* | revisar/NA | revisar/NA | revisar/NA | no detectado* | desconocido | BLOCKED |
| `/registroPacientes/odontograma/<int:id>/` | GET/POST u otros: revisar | middleware* | middleware* | scoped/owned* | No detectada* | revisar/NA | revisar/NA | revisar/NA | no detectado* | desconocido | BLOCKED |
| `/registroPacientes/odontograma/guardar/<int:paciente_id>/` | POST | middleware* | middleware* | scoped/owned* | POST: revisar | Sí* | mapeado* | save_record* | no detectado* | desconocido | BLOCKED |
| `/registroPacientes/progreso/<int:paciente_id>/` | GET/POST u otros: revisar | middleware* | middleware* | scoped/owned* | No detectada* | revisar/NA | revisar/NA | revisar/NA | no detectado* | desconocido | BLOCKED |
| `/registroPacientes/estudio/<int:paciente_id>/` | GET/POST u otros: revisar | middleware* | middleware* | scoped/owned* | POST: revisar | revisar/NA | revisar/NA | revisar/NA | revisar* | desconocido | BLOCKED |
| `/registroPacientes/estudio/<int:paciente_id>/visualizar/` | GET/POST u otros: revisar | middleware* | middleware* | scoped/owned* | No detectada* | revisar/NA | revisar/NA | revisar/NA | no detectado* | desconocido | BLOCKED |
| `/registroPacientes/estudio/<int:paciente_id>/descargar-pdf/` | GET/POST u otros: revisar | middleware* | middleware* | revisar/NA | No detectada* | revisar/NA | revisar/NA | revisar/NA | revisar* | desconocido | BLOCKED |
| `/registroPacientes/consentimiento/<int:paciente_id>/` | GET/POST u otros: revisar | middleware* | middleware* | scoped/owned* | POST: revisar | revisar/NA | mapeado* | revisar/NA | revisar* | desconocido | BLOCKED |
| `/menu_citas/` | GET/POST u otros: revisar | middleware* | middleware* | scoped/owned* | No detectada* | revisar/NA | revisar/NA | revisar/NA | no detectado* | desconocido | BLOCKED |
| `/menu_citas/nueva_cita/` | GET/POST u otros: revisar | middleware* | middleware* | revisar/NA | No detectada* | revisar/NA | revisar/NA | revisar/NA | no detectado* | desconocido | BLOCKED |
| `/menu_citas/registrar_cita/<int:id>/` | GET/POST u otros: revisar | middleware* | middleware* | scoped/owned* | POST: revisar | Sí* | mapeado* | revisar/NA | no detectado* | desconocido | BLOCKED |
| `/menu_citas/buscar_cita/` | GET/POST u otros: revisar | middleware* | middleware* | scoped/owned* | No detectada* | revisar/NA | revisar/NA | revisar/NA | no detectado* | desconocido | BLOCKED |
| `/menu_citas/editar_cita/<int:id>/` | GET/POST u otros: revisar | middleware* | middleware* | scoped/owned* | POST: revisar | Sí* | mapeado* | revisar/NA | no detectado* | desconocido | BLOCKED |
| `/menu_citas/citas_pendientes/` | GET/POST u otros: revisar | middleware* | middleware* | scoped/owned* | No detectada* | revisar/NA | revisar/NA | revisar/NA | no detectado* | desconocido | BLOCKED |
| `/menu_citas/citas_completadas/` | GET/POST u otros: revisar | middleware* | middleware* | scoped/owned* | No detectada* | revisar/NA | revisar/NA | revisar/NA | no detectado* | desconocido | BLOCKED |
| `/menu_citas/citas_canceladas/` | GET/POST u otros: revisar | middleware* | middleware* | scoped/owned* | No detectada* | revisar/NA | revisar/NA | revisar/NA | no detectado* | desconocido | BLOCKED |
| `/menu_citas/confirmar_asistencia/<int:id>/` | POST | middleware* | middleware* | scoped/owned* | POST: revisar | Sí* | mapeado* | revisar/NA | no detectado* | desconocido | BLOCKED |
| `/menu_citas/cancelar_cita/<int:id>/` | POST | middleware* | middleware* | scoped/owned* | POST: revisar | Sí* | mapeado* | revisar/NA | no detectado* | desconocido | BLOCKED |
| `/menu_citas/detalle_cita/<int:id>/` | GET/POST u otros: revisar | middleware* | middleware* | scoped/owned* | No detectada* | revisar/NA | revisar/NA | revisar/NA | no detectado* | desconocido | BLOCKED |
| `/diagnosticos/` | GET/POST u otros: revisar | middleware* | middleware* | scoped/owned* | No detectada* | revisar/NA | revisar/NA | revisar/NA | revisar* | desconocido | BLOCKED |
| `/diagnosticos/resultados/<int:imagen_id>/` | GET/POST u otros: revisar | middleware* | middleware* | scoped/owned* | POST: revisar | Sí* | revisar/NA | revisar/NA | revisar* | desconocido | BLOCKED |
