# Upstash Redis

El plugin de Upstash se instala con `npx -y upstash setup --yes --codex`. Reiniciar Codex para que aparezcan sus herramientas MCP y autorizar la cuenta con permisos de escritura. Como alternativa, ejecutar `npx -y upstash login` en una terminal; las credenciales de administración quedan fuera del repositorio. No pegarlas en chats ni comandos compartidos.

## Base del proyecto

Base creada: `smilemanager-demo`. Región primaria: `us-east-2` (Ohio), cerca del proyecto Neon. Plan `free`, TLS activado, eviction y auto-upgrade deshabilitados. Las credenciales REST y la conexión Redis TLS de Django están en `.env` privado. No activar eviction para el limitador de Django. La conexión MCP se limitó a `https://mcp.upstash.com/mcp?features=redis` para cargar sólo sus herramientas.

Guardar los valores reales emitidos por Upstash en `.env` privado:

```dotenv
UPSTASH_REDIS_REST_URL=https://YOUR-ENDPOINT.upstash.io
UPSTASH_REDIS_REST_TOKEN=YOUR-PRIVATE-REST-TOKEN
THROTTLE_REDIS_URL=rediss://default:YOUR-REDIS-PASSWORD@YOUR-ENDPOINT.upstash.io:6379
```

No confundir el token REST con la contraseña Redis. No versionar `.env` ni usar prefijos `VITE_` para estas variables.

## Cliente TypeScript

`lib/redis.ts` inicializa `@upstash/redis` con `Redis.fromEnv()`. Es para Node.js en el servidor y no se importa desde React. Cargar las variables antes de importar el cliente. La aplicación actual es Django: sus rutas y políticas no cambian al instalar este SDK.

```bash
npm run redis:verify
```

Con el ejecutor TypeScript `tsx`, el comando carga los archivos privados sin sustituir variables del entorno, comprueba PING y escritura/lectura JSON con TTL de 60 segundos y elimina la clave sintética.

## Django

Django sigue utilizando `THROTTLE_REDIS_URL`, el controlador Python Redis y su script atómico existente. No se añade un segundo limitador JavaScript. Tras configurar la conexión TLS, comprobar `/health/ready/` y los tests de integración del limitador (`RATE_LIMIT_TEST_REDIS_URL` contra una base aislada). Configurar sólo las variables REST no habilita los límites de Django.

## Verificación realizada

El cliente TypeScript pasó PING y escritura/lectura JSON con expiración, eliminando la clave de prueba. Django verificó la conexión Redis TLS y su script atómico: dos solicitudes aceptadas y la tercera rechazada. La disponibilidad conjunta de Neon y Upstash se comprueba con `/health/ready/`; esto no verifica correo, antivirus, almacenamiento de archivos ni auditoría externa.
