# SmileIA: servicio de inferencia independiente

La implementación y los pesos se encuentran en `../SmileIA`. SmileManager conserva únicamente el cliente HTTP, la autorización, los registros `AIAnalysisRun` y la publicación en almacenamiento clínico. No requiere PyTorch, Ultralytics ni pesos locales. No hay cambios de esquema ni migraciones.

## Desarrollo con Docker

1. Define `SMILEIA_TOKEN` en un archivo de entorno privado de SmileIA. Usa el mismo secreto en `.local-ops.env` de SmileManager.
2. En `.local-ops.env` configura `SMILEIA_URL=http://smileia:8001` y `FEATURE_AI_ENABLED=true`. La clínica también necesita IA habilitada.
3. Desde SmileManager ejecuta `docker compose --env-file .local-ops.env -f compose.yaml -f compose.ai.yaml up --build -d`. El archivo adicional construye SmileIA desde el proyecto hermano y conecta ambos servicios en la red privada de Compose. El servicio no publica puertos.

Para operar SmileIA en otra máquina, utiliza su propio compose y configura `SMILEIA_URL` con una dirección accesible desde el backend. Usa HTTPS fuera de una red privada de confianza. No publiques el token ni imágenes clínicas en logs. La red local y los secretos deben configurarse antes de solicitar inferencias; el arranque de SmileManager no depende de que SmileIA esté disponible.

## Contrato y fallos

`GET /v1/model` consulta la huella de los pesos. `POST /v1/analyze` envía sólo bytes de imagen y las huellas esperadas de imagen/modelo. Ambas solicitudes llevan autenticación Bearer. La respuesta contiene detecciones e imagen procesada en base64; se limita su tamaño antes de decodificar y publicar.

La versión registrada en el run se exige al servicio: un cambio de pesos entre consulta e inferencia falla sin publicar un resultado con procedencia incorrecta. El hash de entrada se verifica antes de enviar y al recibir en SmileIA. La publicación conserva la revalidación de clínica, membresía, paciente, imagen y estado del run.

`SMILEIA_TIMEOUT` controla el timeout de lectura HTTP (100 s por defecto; conexión 5 s). No es un deadline total ni cancela inferencias remotas. Los errores siguen el manejo de fallos existente; no hay reintentos automáticos. Reinicia SmileIA al cambiar los pesos. El resultado se transfiere síncronamente; no se introduce una cola ni almacenamiento compartido.

## Despliegue y reversión

Reconstruye la imagen de SmileManager para retirar las dependencias de inferencia de imágenes existentes. Despliega SmileIA con el artefacto local `train_model/best.pt` y su secreto. No se requiere migrar la base de datos: el historial y los archivos existentes permanecen accesibles. Deshabilitar `FEATURE_AI_ENABLED` detiene nuevas solicitudes sin eliminar el historial; para revertir el código anterior hay que restaurar también los pesos y dependencias locales desde SmileIA.
