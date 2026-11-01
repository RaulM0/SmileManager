# Arquitectura objetivo

Propuesta incremental: monolito modular Django + DRF, sin microservicios. Los módulos actuales pueden mantenerse mientras se extraen políticas y casos de uso compartidos. Las capas son fronteras prácticas, no una obligación de clases, repositorios o abstracciones por entidad.

```text
React / HTML / integraciones
      ↓
API versionada y adaptadores HTML + admin (validación y contratos)
      ↓
políticas comunes: identidad, pertenencia a clínica, rol y recurso
      ↓
casos de uso por dominio: pacientes / agenda / expediente /
                        archivos / consentimiento / IA
      ↓
ORM + transacciones | storage privado | auditoría | correo / IA
      ↓
PostgreSQL           objetos privados   logs operativos minimizados
```

Definir primero si cada clínica tendrá varios profesionales y qué acceso comparten. En ese caso crear clínica, membresía y roles/atributos, migrar propietarios existentes con validación de datos, y hacer obligatoria la pertenencia en consultas, servicios, exportaciones, jobs y acceso a archivos. Aislar pruebas por clínica, usuario, recurso y acción; definir soporte administrativo sin bypass accidental. La entidad textual actual de perfil no es tenant. Historial y autorización deben sobrevivir a cambios de médico y desactivación de usuario.

Casos de uso deben compartir invariantes entre rutas, validar las relaciones dentro del ámbito permitido y registrar eventos de auditoría en la misma transacción cuando sea posible. Versionado clínico, identidad de autor, correcciones y retención necesitan definición clínica/legal; no introducir inmutabilidad ciega. Los archivos requieren storage privado, entrega autorizada y una estrategia explícita para borrados/reemplazos; la transacción de base no revierte storage, por lo que deben preverse fallos y reconciliación.

El proceso de IA debe guardar estado, versión/hash de modelo, fecha, actor, versión de entrada y resultados cuando negocio lo requiera; demostrar validación clínica del modelo independientemente del código. Limitar concurrencia ya; pasar a job persistente y workers cuando la latencia medida, disponibilidad o reintentos lo justifiquen. Proteger temporales y evitar logs de imágenes. Los permisos y el registro de audit se aplican también al worker.

## Capacidades evaluadas

| Capacidad | Decisión | Justificación |
|---|---|---|
| RBAC y propiedad/ámbito | Necesaria ahora | Mínimo privilegio; definir roles reales y seguridad por recurso. Tenant antes de múltiples clínicas. |
| Audit log y versiones | Necesaria ahora | Reconstrucción y responsabilidad clínica; acordar detalle y retención. |
| Storage privado | Necesaria ahora | Archivos clínicos e identificaciones, SEC-003/004. Signed URLs: recomendables después si se descargan directamente y el bucket es privado; FileResponse puede bastar inicialmente. |
| TLS, backups y restauración | Necesaria ahora | Disponibilidad y confidencialidad demostrables con pruebas. |
| Logging estructurado, métricas, health checks y alertas | Necesaria ahora, proporcionales | Detectar errores de DB/IA, latencia y fallos; no incluir contenido clínico. Tracing distribuido recomendable después si la complejidad lo exige. |
| Handler central y OpenAPI | Recomendable después de P0 | Contrato uniforme y documentación; mantener excepciones internas fuera de respuestas. |
| Versionado API | Presente (`v1`); mantener | Útil para cambios incompatibles, no duplicar versiones sin necesidad. |
| MFA | Recomendable según evaluación de riesgo, especialmente administradores | Reduce riesgo de credenciales robadas; decisión operativa y recuperación. |
| Celery y broker Redis/RabbitMQ | No necesarios actualmente sin métricas | Inferencia síncrona ya es riesgo; introducir cola persistente si SLA, carga o reintentos lo justifican; elegir broker por operación, no por moda. |
| Caché/Redis | No necesario actualmente | Optimizar paginación/consultas primero; cachear datos sensibles exige ámbito e invalidación. |
| Object storage | Recomendable según operación; S3 ya configurado | Privacidad, disponibilidad y backups importan más que cambiar de proveedor. |
| Kubernetes/microservicios | No necesarios actualmente | No hay evidencia de beneficio que compense su complejidad. |
