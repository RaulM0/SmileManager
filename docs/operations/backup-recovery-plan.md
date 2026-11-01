# Plan de backup y recuperación

**Estado: INFRASTRUCTURE VERIFICATION REQUIRED.** El repositorio no demuestra que existan copias ni restauraciones. **BUSINESS DECISION REQUIRED:** RPO, RTO, frecuencia y retención definitivos; no se asignan valores sin aprobación. Propietarios de negocio, clínicos, seguridad y operaciones deben definirlos para cada entorno.

## Aplicación

Registrar versiones de esquema/migraciones, aplicación y configuración necesarias para restaurar. Inventariar referencias DB→objetos (originales, resultados IA, estudios, consentimiento y PDFs); conservar un manifiesto sin divulgar información clínica. DB y almacenamiento no comparten una transacción de backup: establecer una ventana o estrategia de consistencia que permita reconstruir ambos y detectar referencias faltantes o archivos huérfanos. No ejecutar migraciones destructivas durante una recuperación sin validación y respaldo.

## Infraestructura

- PostgreSQL: copias automatizadas cifradas y, si el RPO aprobado lo exige, archivado continuo/WAL y restauración a punto en el tiempo. Aislar copias de producción, claves y permisos; registrar frecuencia, retención, integridad y alertas.
- Object storage: versionado y/o copias en cuenta o ubicación aislada con retención, cifrado y acceso mínimo; versionado no sustituye backup independiente. Incluir todas las categorías y probar recuperación de versiones borradas.
- Definir protección frente a borrado malicioso, acceso administrativo, recuperación de claves y expiración, con responsabilidades y auditoría. Verificar región y restricciones acordadas.

## Restauración y simulacro

1. Autorizar y crear entorno aislado, sin enviar correos ni permitir acceso público; restaurar DB y objetos correspondientes usando credenciales mínimas.
2. Verificar tiempos reales frente a RPO/RTO acordados, migraciones, consistencia de referencias, conteos y muestras autorizadas de cada clase de archivo. Probar autenticación y permisos sin usar datos reales fuera del entorno controlado.
3. Registrar fecha, responsables, versión, fuente, resultados, desviaciones y acciones. Destruir copias temporales conforme a política aprobada.
4. Repetir con periodicidad aprobada y después de cambios relevantes; alertar si falla backup o simulacro.

Una copia **no se considera válida** hasta completar y documentar una restauración verificada. No se realizó restauración en esta fase.
