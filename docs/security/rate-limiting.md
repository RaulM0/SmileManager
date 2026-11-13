# Límites compartidos y protección contra abuso

La producción requiere `THROTTLE_REDIS_URL=rediss://...` (o `redis://` sobre red privada protegida). Sin URL válida la configuración falla al iniciar. Todos los workers deben usar la misma instancia, base, secreto y prefijo; no compartir esa base con cachés que puedan borrarse. Conexión/lectura tienen timeouts de dos segundos. No registrar URL ni credenciales.

`api/rate_limit.py` ejecuta una ventana deslizante mediante Lua atómico, reloj Redis, conjunto ordenado y expiración. Identificadores convertidos en HMAC, sin contraseñas. Rechazos no extienden ventanas. Login tiene ventanas por cuenta e IP; recuperación por email/IP; sesión y refresh por IP; IA/correo/exportaciones por usuario. Fallos de Redis devuelven 503 sin continuar la operación protegida; excesos devuelven 429 con `Retry-After`. Readiness comprueba Redis.

Desarrollo/pruebas pueden usar caché local cuando no hay URL; no ofrece coordinación y no se admite con settings de producción. Las pruebas de integración requieren `RATE_LIMIT_TEST_REDIS_URL` de una instancia aislada, con prefijos únicos y limpieza de sus claves. No apuntarla a producción.

## Proxy

Por defecto se usa `REMOTE_ADDR`. `X-Forwarded-For` se ignora salvo peer en `THROTTLE_TRUSTED_PROXIES`, lista de IP/CIDR explícitos separada por comas, sin `/0`. Se recorre de derecha a izquierda hasta el primer salto no confiable. Cadenas inválidas o demasiado largas se rechazan; acepta IPv4/IPv6.

No confiar en redes amplias compartidas con clientes. El proxy debe sobrescribir/agregar correctamente la dirección y no admitir rutas alternativas desde peers confiables. Sin cabecera se usa el peer, que puede agrupar clientes: probar topología real. Esta configuración es independiente de `TRUST_PROXY_HTTPS_HEADER`.

## Operación antes de producción

- Redis privado, TLS según arquitectura, ACL para `EVAL`, `TIME`, `ZREMRANGEBYSCORE`, `ZCARD`, `ZRANGE`, `ZADD`, `PEXPIRE`, `PING` y comandos de conexión/autenticación del cliente.
- Memoria suficiente, `noeviction`, persistencia y alarmas. Borrado, reinicio o failover con pérdida de estado puede reiniciar ventanas: mantener protección de borde.
- Limitar conexiones, cuerpos, frecuencia y concurrencia en proxy/WAF. Redis no sustituye defensa DDoS.
- Alertas de 429/503 y pruebas de varios workers, proxy y recuperación. El bloqueo por cuenta sigue pudiendo ocasionar denegación dirigida temporal.
- Valores iniciales: auth `30/min`, cuenta `10/min`, recuperación IP `10/hour`, cuenta `3/hour`, confirmación `20/hour`; IA/correo/exportación `10/min`. Variables `THROTTLE_*` en settings; ajustar con evidencia.

Instalar `redis==8.1.0` y provisionar Redis antes de arrancar producción. Reversión: versión anterior con revisión de riesgo; no usar settings locales en producción. No se configuró infraestructura real en esta etapa.

Referencias: [atomicidad Redis](https://redis.io/docs/latest/develop/programmability/eval-intro/), [límites DRF](https://www.django-rest-framework.org/api-guide/throttling/).
