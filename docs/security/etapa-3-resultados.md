# Etapa 3: controles operativos de seguridad

## Alcance y estado

Implementación local de desarrollo. Los datos del simulacro son sintéticos; no se desplegó a producción. Esta etapa aborda MX07 (auditoría), MX09 (archivos) y parte de MX08 (operación y recuperación). No constituye certificación ni aprobación regulatoria para México.

## Controles implementados

- **Auditoría:** UUID y sello HMAC por evento nuevo; bloqueo de modificaciones desde el ORM y mediante trigger PostgreSQL. Los eventos históricos permanecen sin sello y se identifican como tales; no se inventa evidencia retrospectiva.
- **Copia separada:** exportación reintentable e idempotente hacia un recolector privado, con almacenamiento SQLite en otro volumen. Encadenamiento SHA-256 y triggers contra actualización/eliminación. La aplicación no tiene montado ese volumen ni dispone de una API para borrar entradas. La entrega usa acuses individuales, evitando perder transacciones que confirmen fuera de orden.
- **Denegaciones:** eventos de acceso denegado sin copiar cuerpos, encabezados, rutas ni identificadores enviados por usuarios no autorizados.
- **PDF:** cuarentena privada hasta completar ClamAV y análisis estructural en un subproceso con límites de memoria, CPU y tiempo. Se rechazan contenido activo, adjuntos, cifrado, estructuras inválidas y discrepancias de hash. Fallas del antivirus o firmas de más de tres días mantienen el bloqueo. Los bytes originales se conservan.
- **Descargas:** autorización de clínica/paciente, integridad del documento y hash del archivo; un resultado CLEAN requiere sello válido. También se bloquean PDF históricos pendientes de inspección. Las imágenes mantienen validación Pillow.
- **Operación:** Redis compartido, trabajador de exportación/escaneo, alertas estructuradas sin datos clínicos y comando de comprobación con salida distinta de cero ante incidencias.
- **Respaldo:** base PostgreSQL, archivos privados y copia de auditoría en un paquete AES-256-GCM. Se detienen temporalmente los escritores y se reinician al finalizar. Un respaldo alterado no libera texto descifrado. Las claves se conservan aparte.
- **Recuperación:** restauración en base y volumen nuevos, red Docker interna y sin puertos publicados. Se contrastan conteos, archivos referenciados, hashes y sellos. Los recursos del simulacro se eliminan al terminar.

## Evidencia local

La suite completa de backend pasó 292 pruebas con PostgreSQL, Redis y ClamAV reales, incluido el patrón inocuo EICAR. Después se verificaron 13 pruebas focalizadas de etapa 3, incluidas dos nuevas regresiones sobre firmas vencidas y conservación de archivos rechazados. Pasaron 58 pruebas de frontend y los 12 escenarios de navegador; TypeScript, ESLint y compilación también pasaron. Se creó evidencia PDF sintética y se comprobó su conservación en respaldo. Los resultados finales y comandos reproducibles se describen en [operación de etapa 3](../operations/etapa-3-local.md).

El primer respaldo tomó 38,41 segundos y su restauración aislada 15,26 segundos. La restauración del respaldo automático posterior, que incluye el PDF sintético y dos eventos encadenados, pasó en 21,51 segundos; el temporizador del usuario confirmó una ejecución con salida 0. Son mediciones de una base pequeña de desarrollo; no establecen RPO/RTO de producción. Los informes de los siguientes simulacros quedan en `.local-backups/*.restore.json`, fuera de Git.

## Límites y siguientes pasos

El propietario del host, un superusuario PostgreSQL o quien controle las claves puede superar controles locales. La cadena local no es almacenamiento WORM ni prueba independiente contra truncamiento por el administrador del host. La copia continúa en la misma máquina: falta establecer custodia externa, retención, recuperación ante pérdida del equipo, monitoreo atendido y pruebas periódicas con volúmenes representativos.

Antes de producción deben asignarse responsables y objetivos RPO/RTO, separar identidades y privilegios de aplicación/operación, custodiar y rotar claves reales, validar TLS/redes/almacenamiento y completar los procedimientos y revisión normativa de cada clínica. El temporizador local funciona mientras esté disponible el gestor de servicios del usuario y Docker; no sustituye una plataforma de respaldos de producción.
