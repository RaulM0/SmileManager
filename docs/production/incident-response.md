# Respuesta técnica a incidentes

Asignar responsables y medios de contacto fuera de este documento. Registrar tiempos y decisiones sin copiar datos clínicos innecesarios.

1. Detectar y preservar evidencia: request IDs, auditoría, logs técnicos, versiones y estado de acceso; protegerlos contra modificación.
2. Contener según incidente: deshabilitar cuenta/tokens, restringir bucket, detener worker IA o aislar despliegue. No borrar evidencia ni archivos clínicos.
3. Revocar y rotar secretos o sesiones comprometidas; revisar accesos y copias, incluidos Git y backups. Confirmar que la revocación de `AuthSession` impide usar access y refresh en su siguiente validación. No retira respuestas ya entregadas ni cancela retroactivamente solicitudes autorizadas. Conservar claves documentales y de MFA necesarias para recuperación; seguir la [etapa 2](../security/etapa-2-resultados.md).
4. Recuperar desde copia probada y reconciliar DB/objetos. Para fallo de backup, corregir y ejecutar restore documentado; para RUNNING de IA seguir [ciclo IA](../architecture/ai-analysis-lifecycle.md).
5. Informar a los responsables de seguridad, clínica y operación; decisiones de notificación a pacientes o autoridades: **LEGAL/ORGANIZATIONAL REVIEW REQUIRED**.

Alertas mínimas: 5xx, DB y readiness, storage, fallos y runs antiguos de IA, backups y simulacros fallidos, y abuso de autenticación. **MONITORING INFRASTRUCTURE REQUIRED**: no se encontró proveedor de alertas configurado en el repositorio.
