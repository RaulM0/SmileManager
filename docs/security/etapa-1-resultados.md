# Etapa 1 — Contención, límites compartidos y escaneos

Cambios realizados después de aprobar el plan de la auditoría del 8 de noviembre de 2026. Alcance: MX-01, MX-05 y escaneos iniciales de MX-10. No representa cierre de las otras etapas ni aprobación para producción.

## Resultado por hallazgo

| Hallazgo | Implementación | Pendiente para cierre completo |
|---|---|---|
| MX-01 | 276 archivos de `media/` y una base vacía retirados del índice; las 277 copias locales siguen presentes. Comprobación de categorías sensibles incorporada a CI. | Clasificar contenido con el responsable; revisar distribución y copias; limpieza histórica coordinada si corresponde. Hacer obligatorio el job en protección de ramas. |
| MX-05 | Ventana deslizante Redis atómica, HMAC para identificadores, rechazo 503 ante indisponibilidad, respuesta 429 con espera, proxies explícitos y readiness con Redis. | Provisionar y proteger Redis, verificar proxy real, límites perimetrales, persistencia/failover y alertas. |
| MX-10, escaneos iniciales | npm, paquetes Python y Gitleaks ejecutados con los resultados descritos abajo. | Escaneo del sistema operativo de la imagen, SBOM, reproducibilidad y evidencia de ejecución en CI remoto. |

Las bajas de archivos están preparadas en el índice de Git; las modificaciones de código quedan visibles en el árbol de trabajo. No se creó commit, no se publicó ni se reescribió historial. Se conservó el cambio preexistente de `frontend/package-lock.json`.

## Implementación

- `scripts/check_sensitive_tracking.py` examina el índice sin abrir contenidos ni imprimir nombres. Bloquea carpetas clínicas, bases locales, archivos de entorno y claves privadas; permite la plantilla `.env.example`.
- CI añade el job `sensitive-files` y un servicio Redis de pruebas. No se modificó la protección de ramas del proveedor.
- `api/rate_limit.py` consume ventanas mediante Lua y reloj Redis; contadores compartidos y expiración. Los rechazos no prolongan el bloqueo. Las claves no contienen direcciones o nombres de cuenta en claro.
- `api/throttles.py` usa Redis para los ámbitos existentes de autenticación, recuperación, IA, correo y exportaciones. La caché local queda disponible para desarrollo/pruebas sin URL.
- La configuración de producción requiere `THROTTLE_REDIS_URL`. La lista `THROTTLE_TRUSTED_PROXIES` valida redes explícitas, rechaza `/0` y no confía en cabeceras de peers ajenos.
- `api/health.py` comprueba Redis en readiness cuando está configurado y devuelve un error genérico si no responde.
- Nueva dependencia: `redis==8.1.0`. No se modificaron modelos ni se añadieron migraciones.

## Validación ejecutada

Se utilizó una copia temporal de la imagen local de la aplicación con el cliente Redis y pip-audit instalados. El repositorio se montó de solo lectura. Bases, archivos y servicios de prueba aislados; sin usar PostgreSQL, media o correo del contenedor existente.

| Comprobación | Resultado |
|---|---|
| Suite backend con SQLite temporal y Redis | 262 pruebas, OK; 21 omitidas por condiciones del motor o del entorno |
| Suite backend con PostgreSQL temporal y Redis | 262 pruebas, OK; ninguna omitida |
| Concurrencia Redis | Pruebas de 40 intentos paralelos con cuota de 5, y cuatro procesos independientes con cuota compartida de 7: aprobadas |
| Otros contratos | Expiración, conexión nueva, separación de ámbitos, `Retry-After`, IP falsificada, cadena IPv6, error 503 sin detalles internos y readiness: aprobados |
| Configuración | Producción sin Redis y redes de proxy inválidas rechazadas por pruebas |
| Índice Git | Cero archivos en categorías bloqueadas; 277 bajas y 277 copias locales conservadas |
| Estilo de diff | `git diff --check` y variante `--cached`: sin errores |
| Dependencias instaladas | Coinciden las versiones públicas de todos los pins de `requirements.txt`; `pip check`: sin conflictos |

Comandos de suite reproducibles con dependencias instaladas y servicios **aislados** accesibles:

```bash
DJANGO_SETTINGS_MODULE=SmileManager.settings_test RATE_LIMIT_TEST_REDIS_URL=redis://127.0.0.1:6379/15 python manage.py test --noinput
DJANGO_SETTINGS_MODULE=SmileManager.settings_postgres_test RATE_LIMIT_TEST_REDIS_URL=redis://127.0.0.1:6379/15 PHASE2_TEST_DATABASE_URL=postgresql://USUARIO:CLAVE@HOST:PUERTO/postgres python manage.py test --noinput
python scripts/check_sensitive_tracking.py
```

La configuración PostgreSQL crea una base de pruebas con nombre aleatorio y la destruye al terminar. No usar conexiones de producción. El comando del índice requiere el estado de bajas preparado o confirmado en Git para pasar.

## Escaneos

- `npm audit --json --registry=https://registry.npmjs.org`: **0 avisos**, 339 dependencias reportadas, incluidas de desarrollo; sin correcciones automáticas del lock.
- pip-audit 2.10.1 sobre la imagen temporal: **0 avisos en paquetes auditables**. La herramienta omitió `torch 2.13.0+cpu` y `torchvision 0.28.0+cpu` por no encontrarlos con esos identificadores en PyPI.
- Comprobación complementaria sin resolver dependencias sobre las versiones públicas `torch==2.13.0` y `torchvision==0.28.0`: **0 avisos**. Esto consulta advisories de esas versiones; no valida el contenido binario de las ruedas CPU.
- Gitleaks 8.24.3 en historial de todas las referencias locales: **0 hallazgos**. Hay 77 commits accesibles en las referencias locales; no se consultaron copias remotas, forks o clones.
- Gitleaks en árbol actual: **0 hallazgos** tras reformular una frase del informe que disparaba la regla genérica de API key. Se examinó únicamente su reporte redactado para clasificarla; no se agregaron exclusiones. Se mantuvo la configuración existente que excluye medios clínicos y ciertos directorios generados, y el límite de 2 MB por archivo.

Los resultados dependen de las bases de avisos consultadas y de ese alcance. No acreditan inexistencia de vulnerabilidades, ausencia de datos personales en archivos ni saneamiento histórico. No se realizó un escaneo de CVE del sistema operativo del contenedor ni una prueba E2E de navegador en esta etapa; no hubo cambios de frontend.

## Despliegue y reversión

**No desplegar sin provisionar Redis.** La versión nueva no inicia con settings de producción si falta su URL. Todos los workers deben compartir instancia/base/secreto, con ACL mínima, transporte protegido, memoria suficiente, `noeviction`, persistencia y alertas. Redis de CI es temporal y no es una plantilla de producción.

Configurar proxies solo después de verificar la topología; por defecto se ignoran cabeceras reenviadas. Establecer límites complementarios en el borde. Ver [operación de límites](rate-limiting.md).

La reversión de código requiere volver a la versión anterior y documentar que reaparece la limitación por proceso. No activar settings locales para evitar el requisito Redis en producción. La retirada de archivos del índice no debe revertirse como mecanismo de recuperación: las copias locales se conservaron.

Los contenedores temporales de Redis y PostgreSQL se retiran al finalizar las verificaciones; no se alteran los contenedores existentes de la aplicación.

## Siguiente etapa

MX-02, MX-03, MX-04 y MX-06 requieren el flujo de aceptación aprobado, datos jurídicos del responsable y la matriz de documentos y firmas. MX-07 a MX-10 conservan las verificaciones operativas y regulatorias señaladas en el informe original. El dictamen general permanece NO-GO hasta reunir la evidencia pendiente.
