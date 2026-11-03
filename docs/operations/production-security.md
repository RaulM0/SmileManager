# Acciones de infraestructura para producción

**Readiness:** no desplegar datos clínicos reales hasta resolver el bypass de admin y verificar controles externos de [go-live](../production/go-live-checklist.md). W005/W021 requieren decisión sobre todos los subdominios y preload; no se silencian ni habilitan sin pruebas. Recuperación de runs IA: consultar [procedimiento](../architecture/ai-analysis-lifecycle.md); el operador debe detener y comprobar todos los workers antes de aplicar.

**INFRASTRUCTURE ACTION REQUIRED.** Antes de usar datos clínicos: confirmar S3 Block Public Access en cuenta y bucket, ausencia de políticas/ACL públicas, acceso IAM mínimo, cifrado y claves, y probar acceso anónimo y entre identidades a objetos conocidos. La configuración Django no cambia la política del bucket ni revoca URLs antiguas. Invalidar cachés y revisar CDN/proxy; nunca exponer `/media/` ni servir el directorio local directamente.

Configurar `SECRET_KEY` fuerte y exclusiva, `DATABASE_URL`, `AWS_STORAGE_BUCKET_NAME`, `ALLOWED_HOSTS` explícitos y `CSRF_TRUSTED_ORIGINS` según dominios. Activar `TRUST_PROXY_HTTPS_HEADER=true` únicamente cuando el reverse proxy confiable elimine cualquier encabezado entrante `X-Forwarded-Proto` y establezca el suyo; verificar cadena TLS/proxy, redirección y cookies en despliegue real. Sin proxy confiable, no activar esa opción y terminar TLS directamente. HSTS se configura para el dominio principal; `includeSubDomains` y preload permanecen desactivados hasta comprobar todos los subdominios y aceptar sus consecuencias. Revisar rotación, origen y custodia de claves; verificar que ninguna cuenta de ejemplo esté activa.

`check --deploy` aislado emitió W005 y W021: subdominios y preload no se activan sin verificación de infraestructura. No fueron silenciados. Verificar backups y restauración según [plan](backup-recovery-plan.md). La configuración segura de Django no demuestra cumplimiento legal ni seguridad del proveedor.
# Recuperación de contraseña

La recuperación requiere `FRONTEND_URL` HTTPS, remitente y SMTP configurados. La entrega síncrona puede filtrar diferencias temporales y el throttling de aplicación no equivale a un control distribuido. Revisar la lista de infraestructura y límites de revocación en [recuperación de contraseña](../security/password-recovery.md).
