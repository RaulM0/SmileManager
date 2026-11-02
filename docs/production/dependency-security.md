# Dependencias y seguridad de suministro

## Actualización de dependencias

Se actualizaron las dependencias afectadas fijadas en `requirements.txt`, entre ellas Django 5.2.18, DRF 3.18.3, Pillow 13.0.0, Torch 2.13.0 con torchvision 0.28.0 y Ultralytics 8.3.253. Se fijó pypdf y se actualizaron las versiones afectadas de AWS SDK, requests y sus dependencias. El entorno de prueba se instaló por separado; `pip check` no encontró incompatibilidades y `pip-audit` sobre todos sus paquetes instalados, incluidas transitivas y el propio escáner, informó **0 vulnerabilidades conocidas** en el momento de la prueba. Los avisos posteriores pueden cambiar este resultado; las versiones sin hashes siguen siendo una limitación de reproducibilidad.

Se actualizó ESLint a 10.14.0, su configuración y el plugin React a versiones compatibles y se aplicó un override a minimatch 11.0.1. Se verificaron `npm ci`, `npm audit` (0 avisos), lint, typecheck, pruebas y build. El override fuerza una versión mayor respecto a los rangos declarados por algunas herramientas, por lo que debe revisarse al actualizar ESLint y no garantiza que todos los usos posibles de esas herramientas sean compatibles.

La batería Django pasó con SQLite temporal, las pruebas de concurrencia con PostgreSQL temporal y el modelo local produjo una inferencia sobre una imagen sintética. Una prueba E2E en navegador/HTTP también pasó usando el entorno actualizado, con análisis IA y autorización entre usuarios. No se utilizaron datos clínicos reales. El workflow audita el entorno instalado, incluidas transitivas, y ejecuta `pip check`, evitando instalar una segunda copia del árbol de Torch/CUDA. Su ejecución real en GitHub todavía debe comprobarse.

Las secciones siguientes conservan los resultados **históricos anteriores a esta actualización**. Este escaneo no certifica que la aplicación sea segura ni cierra los controles de infraestructura, operación o retención pendientes.

## Escaneo de cierre

`pip-audit` 2.10.1 sobre el entorno instalado informó **196 registros de avisos en 15 paquetes**; puede haber advisories solapados y el entorno incluye herramientas de desarrollo. No se declara severidad porque la salida utilizada no la proporciona. Incluye Django 5.2.8, DRF 3.16.1, Pillow 12.0.0, Torch 2.9.1 y urllib3 2.5.0. Lista completa de paquetes, IDs y versiones de corrección en [python-dependency-audit.md](python-dependency-audit.md). Es un bloqueo de evaluación/remediación; no se hicieron upgrades ciegos ni se asegura que una sola versión corrija todos los avisos.

Gitleaks 8.24.3 con salida redactada: 53 commits de todas las refs locales, sin hallazgos; árbol de trabajo filtrado, sin hallazgos. El árbol excluye `.venv`, `node_modules`, media clínica, DB, artefactos y archivos >2 MB; no equivale a prueba de inexistencia de secretos ni cubre remotos no disponibles. La presencia de DB/media rastreadas requiere igualmente remediación. No se verificaron secretos en producción.

En la ejecución local `npm audit --omit=dev` informó 0 vulnerabilidades; `npm audit` completo informó 12 moderadas en la cadena de desarrollo (minimatch y dependientes ESLint/TypeScript ESLint), [GHSA-g3hv-75wg-m249](https://github.com/advisories/GHSA-g3hv-75wg-m249). `npm ls` muestra minimatch 3.1.5 y 10.2.6. El conteo incluye dependientes y no significa 12 fallos independientes. No ejecutar `npm audit fix --force` sin evaluar compatibilidad. Repetir el escaneo en CI.

`pip-audit` no estaba instalado; vulnerabilidades Python **NO VERIFICADAS**. `requirements.txt` fija versiones, pero no aporta lock con hashes; `frontend/package-lock.json` fija el árbol JS para `npm ci`. No se revisaron artefactos de imágenes de contenedor mediante escáner. No se encontró pipeline de CI en el repositorio; comprobar si existe externamente.
