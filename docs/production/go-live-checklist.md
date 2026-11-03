# Go-live: criterios verificables

Antes de habilitar el backoffice, designar responsables, asignar explícitamente el permiso y verificar los procesos de alta/baja de administradores, monitoring, custodia de audit y recuperación de acceso. El panel no sustituye los controles externos de esta lista.

**Actualización:** el bypass clínico de ModelAdmin se mitigó; falta validar las concesiones reales de permisos. Las dependencias se actualizaron y los escaneos locales no detectaron avisos conocidos; verificar su instalación y auditoría en CI Linux. La ejecución completa de E2E/legacy y los controles externos de abajo permanecen pendientes.

**NO-GO** hasta cerrar: bypass administrativo de servicios y versiones clínicas; distribución de datos sensibles en Git y copias remotas; prueba de privacidad de storage; restauración conjunta DB/objetos; y validación E2E crítica y controles de acceso en el despliegue. También NO-GO ante DEBUG activo, secreto real expuesto sin rotación, BOLA, archivos públicos, fallo de migración o ausencia de capacidad operativa para responder incidentes.

Antes de autorizar el despliegue, responsables designados deben aportar evidencia de:

- TLS, proxy que sustituye `X-Forwarded-Proto`, host, límites multipart y timeouts; HSTS subdominios/preload requiere decisión de infraestructura.
- Bucket privado: Block Public Access, políticas, ACL, IAM mínimo, cifrado, versionado, lifecycle y pruebas anónima/autorizada con objeto sintético.
- PostgreSQL: cifrado, roles mínimos, límites, backups, PITR donde aplique y restauración probada junto con archivos; no usar superusuario para la aplicación.
- Monitorización y alertas de 5xx, DB/readiness, storage, IA fallida/RUNNING antiguo, backup/restore y abuso de autenticación.
- Secretos en gestor, historial Git y clones tratados, dependencias examinadas, migraciones y rollback ensayados, y pipeline con pruebas y aprobación.
- Operación, acceso administrativo, protección perimetral de login, retención y auditoría aprobados por responsables.

RPO/RTO: **BUSINESS DECISION REQUIRED**. Retención y correcciones clínicas: **CLINICAL/LEGAL REVIEW REQUIRED**. La inexistencia de Celery o Redis no es por sí misma un bloqueo.
# Backoffice clínico global

- [ ] Aprobar el alcance de lectura global y revisar cada asignación de `access_system_backoffice`.
- [ ] Validar con clínica/legal los datos accesibles y las reglas de conservación y consulta.
- [ ] Verificar rendimiento y alertas de auditoría sobre infraestructura aislada representativa.
# Recuperación de contraseña

- [ ] Verificar URL HTTPS del frontend, remitente, entrega SMTP, SPF/DKIM/DMARC y alertas.
- [ ] Aprobar mitigación de diferencias temporales y límites por IP/cuenta para la topología real.
- [ ] Aceptar o cambiar la ventana residual de access JWT y revisar las cuentas con correo duplicado.
