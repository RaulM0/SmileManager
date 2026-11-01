# Línea base sintética local — antes de optimizaciones

**LOCAL BENCHMARK — NO PRODUCTION CAPACITY CLAIM.** PostgreSQL en contenedor local, cliente de pruebas Django en el mismo equipo, sin red HTTP real, datos generados sintéticamente. `api/tests/benchmark_synthetic.py` y `run_perf_postgres.py` crean una base temporal de nombre aleatorio y la destruyen; no utilizan DB clínica ni objetos reales. Cada escenario tiene n pacientes y citas, y concentra n consultas e imágenes en un solo paciente para exponer el peor caso de serialización, no para representar una distribución clínica real. Cada muestra corresponde a una petición por tamaño, instrumentada con `tracemalloc`: no es p95 ni un benchmark de throughput. `db_ms` de Django tiene resolución limitada y la instrumentación altera la latencia. Todos los archivos son rutas sintéticas, no archivos clínicos.

| Endpoint | n=10 queries / ms / bytes | n=100 queries / ms / bytes | n=1000 queries / ms / bytes |
|---|---:|---:|---:|
| dashboard | 3 / 125 / 3236 | 3 / 69 / 32129 | 3 / 1369 / 322832 |
| pacientes | 2 / 20 / 2853 | 2 / 17 / 2893 | 2 / 44 / 2894 |
| búsqueda | 2 / 32 / 2853 | 2 / 30 / 2910 | 2 / 66 / 2911 |
| autocomplete | 1 / 17 / 424 | 1 / 16 / 424 | 1 / 37 / 424 |
| detalle paciente | 2 / 18 / 279 | 2 / 16 / 279 | 2 / 30 / 279 |
| antecedentes | 3 / 35 / 668 | 3 / 27 / 668 | 3 / 85 / 668 |
| consultas del paciente | 12 / 58 / 2752 | 102 / 493 / 27593 | 1002 / 6276 / 276894 |
| citas | 1 / 25 / 3493 | 1 / 268 / 35085 | 1 / 1147 / 352787 |
| odontograma vacío | 3 / 20 / 115 | 3 / 40 / 115 | 3 / 28 / 115 |
| imágenes del paciente | 12 / 71 / 2343 | 102 / 1352 / 23585 | 1002 / 6772 / 237787 |
| diagnósticos | 5 / 45 / 2489 | 5 / 100 / 2554 | 5 / 109 / 2577 |
| consentimiento vacío | 4 / 29 / 102 | 4 / 56 / 102 | 4 / 33 / 102 |
| estudio vacío | 3 / 26 / 16 | 3 / 38 / 16 | 3 / 29 / 16 |
| exportación pacientes | 2 / 822 / 5683 | 2 / 390 / 9281 | 2 / 1753 / 43514 |

El primer XLSX incluye inicialización; memoria pico Python trazada en exportación de 1000 fue ~3,7 MB y ~5,1 MB en la primera exportación de 10. Esto no es RSS total ni límite de producción. Consultas e imágenes presentan N+1 confirmado; citas y dashboard serializan listas completas. No se ha medido 10.000 ni IA en esta línea base.

## Comparación posterior

**PROBLEM:** N+1. **EVIDENCE:** 1002 queries para 1000 consultas e imágenes. **CHANGE:** `select_related('paciente')` en cada ruta. **RESULT:** ambas ejecutaron 2 queries para 1000; consultas 6276→1256 ms e imágenes 6772→1387 ms, muestras únicas con instrumentación. Siguen devolviendo toda la colección: falta paginación.

**PROBLEM:** dashboard sin límite. **EVIDENCE:** 1000 citas futuras producían 322832 bytes y 1369 ms. **CHANGE:** listas de hoy y próximas limitadas a `DASHBOARD_APPOINTMENT_LIMIT` (50 por defecto), orden estable y `today_count` independiente. **RESULT:** 16094 bytes y 217 ms, 4 queries en lugar de 3. La UI informa que la lista es parcial. Cifras de una muestra, no garantía de latencia.

**PROBLEM:** exportación síncrona potencialmente grande. **EVIDENCE:** perfil separado 100/1000/10000 filas: 0,683/1,15/14,34 s; 9.260/43.306/378.386 bytes; pico Python 5,40/3,68/38,82 MB; una query en el servicio. El primer caso incluye carga inicial. **CHANGE:** límite configurable `EXPORT_MAX_ROWS=1000`, leído como máximo 1001 filas; responde 413 si se supera. **RESULT:** límite probado funcionalmente, no extrapolar capacidad. El límite es inicial y revisable; exportaciones mayores precisan otro flujo de negocio. El endpoint suma el evento de auditoría.

En el cierre de fase 3, paciente, diagnósticos y autocomplete ya estaban paginados o limitados, pero citas, consultas e imágenes todavía no. La fase 3.1 modifica esos contratos como se describe a continuación; las rutas HTML legacy requieren revisión independiente.

## Fase 3.1 — primera página

En la repetición local con carga concurrente de otros procesos, a 1000 registros: citas 2 queries y 7099 bytes; consultas 3 queries y 5650 bytes; imágenes 3 queries y 4873 bytes. Antes de paginar: 352787, 276894 y 237787 bytes respectivamente. Con 100 registros: 7098, 5629 y 4832 bytes; el payload se mantiene aproximadamente constante. Latencias medidas bajo contención: 125/433/414 ms, muestras individuales no comparables de forma rigurosa. El `COUNT` añade una query frente a los endpoints optimizados sin paginación. Ver [contrato](../api/pagination-contracts.md); el calendario recorre todas las páginas del rango visible y no muestra resultados parciales como completos.
