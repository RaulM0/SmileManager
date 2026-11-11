# Operación local: etapa 3

Este procedimiento corresponde exclusivamente a desarrollo. No utilizar datos reales ni las claves de prueba en producción.

## Arranque

```sh
python3 scripts/setup_dev_security.py
docker compose --env-file .local-ops.env up --build -d
```

La configuración privada se crea con permisos `0600`; una segunda ejecución conserva el archivo existente. El montaje del código oculta este archivo dentro de los contenedores; la clave de respaldo solo se entrega al proceso de cifrado por variable de entorno. Contiene claves independientes de auditoría, inspección y respaldo. No modifica las claves clínicas/MFA anteriores. Respaldar las claves por un canal separado del paquete cifrado y conservar las versiones necesarias para verificar archivos antiguos.

El servicio `audit-init` prepara automáticamente los permisos del volumen independiente antes de iniciar el recolector.

ClamAV necesita hasta 4 GiB, actualiza firmas y no publica puertos al host. Redis y el recolector tampoco publican puertos. El backend aplica las migraciones al arrancar. No exponer el servidor Django de desarrollo a Internet.

## Comprobaciones

```sh
docker compose --env-file .local-ops.env exec -T backend python manage.py check_security_operations
docker compose --env-file .local-ops.env exec -T backend python manage.py verify_audit
docker compose --env-file .local-ops.env exec -T audit-collector python docker/audit_collector.py --verify
docker compose --env-file .local-ops.env logs --tail 50 security-worker
```

`check_security_operations` alerta por trabajador ausente/vencido, respaldo de más de 26 horas, exportación o escaneos demorados, archivos rechazados y ráfagas de denegaciones. `verify_audit` distingue eventos históricos sin sello. Los detalles clínicos y las claves no se imprimen.

Los PDF pendientes devuelven HTTP 423 y la interfaz indica cuarentena. Ante ERROR, revisar disponibilidad del antivirus, actualización de firmas y registros del trabajador; los reintentos ocurren después de cinco minutos. Un reclamo interrumpido vuelve a ser elegible después de diez minutos. REJECTED conserva el original bloqueado: investigar y registrar una evidencia de reemplazo; no cambiar manualmente a CLEAN ni sobrescribir originales. Un cambio de bytes exige una nueva evidencia.

## Respaldo y recuperación

```sh
python3 scripts/dev_backup.py create
python3 scripts/dev_backup.py restore .local-backups/ARCHIVO.smilebackup
```

El respaldo pausa backend/trabajador y restablece los servicios que estaban activos. Los temporales claros viven en un directorio privado y se eliminan al finalizar normalmente. Una interrupción abrupta del sistema puede dejar temporales: revisar `/tmp/smile-backup-*` y `/tmp/smile-restore-*`. Los archivos `.incomplete` no son respaldos válidos. No hay eliminación automática de copias.

La restauración autentica el paquete antes de entregar bytes a PostgreSQL, utiliza una red interna y volúmenes nuevos, verifica el contenido y escribe un informe `.restore.json`. Conserva las claves vigentes de custodia cuando el backend existe; sin ese contenedor, configurar las claves originales en `.local-ops.env` o en el entorno. El código y una imagen compatible deben estar disponibles; puede seleccionarse otra imagen mediante `SMILE_RESTORE_IMAGE`. No restaura sobre la base actual ni levanta correo o servicios clínicos en la copia.

Para reproducir el simulacro con un PDF sin datos reales:

```sh
docker compose --env-file .local-ops.env exec -T backend python manage.py prepare_stage3_drill
docker compose --env-file .local-ops.env exec -T backend python manage.py run_security_jobs --once
```

El comando está restringido a `settings_local` y crea una cuenta sintética inactiva, sin contraseña utilizable.

## Automatización

En este equipo se activó el temporizador diario del usuario. Las unidades asumen el repositorio en `~/repos/SmileManager`; adaptar esa ruta en otros equipos.

```sh
systemctl --user link "$PWD/docker/smilemanager-dev-backup.service" "$PWD/docker/smilemanager-dev-backup.timer"
systemctl --user daemon-reload
systemctl --user enable --now smilemanager-dev-backup.timer
systemctl --user list-timers smilemanager-dev-backup.timer
journalctl --user -u smilemanager-dev-backup.service --no-pager
```

Alternativa portable: `python3 scripts/dev_backup_schedule.py`, que debe permanecer ejecutándose. La programación requiere sesión/gestor del usuario y Docker disponibles. Para detenerla: `systemctl --user disable --now smilemanager-dev-backup.timer`. Comprobar periódicamente restauraciones y capacidad de disco; aún no existe custodia externa ni política automática de retención.
