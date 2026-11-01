# Carga sintética local

`run_perf_postgres.py api.tests.benchmark_load` usa DB PostgreSQL temporal, 1000 pacientes, 100 citas y APIClient secuencial en proceso. 50 solicitudes por escenario; sin HTTP real, latencia de red, concurrencia ni autenticación JWT real (`force_authenticate`). **LOCAL BENCHMARK — NO PRODUCTION CAPACITY CLAIM.** Percentil 99 no se informa: muestra insuficiente. No se mide mezcla simultánea ni conexiones bajo carga distribuida.

| Escenario | req/s en proceso | p50 ms | p95 ms | errores | CPU de proceso s | RSS al final MB |
|---|---:|---:|---:|---:|---:|---:|
| pacientes | 137,56 | 6,74 | 8,96 | 0/50 | 0,20 | 346,0 |
| agenda (100 citas) | 30,42 | 28,96 | 52,14 | 0/50 | 1,38 | 351,9 |
| antecedentes vacíos | 63,06 | 15,18 | 20,13 | 0/50 | 0,55 | 351,9 |
| búsqueda | 55,27 | 17,29 | 23,74 | 0/50 | 0,50 | 352,0 |

El RSS incluye dependencias/modelo y no representa consumo incremental de cada endpoint; CPU es tiempo de proceso, no porcentaje ni medición del servidor PostgreSQL. Faltan mezcla concurrente, red, conexiones DB y tamaños mayores. La inferencia se midió por separado en [IA](ai-inference.md).

## HTTP loopback fase 3.1

`run_perf_postgres.py api.tests.benchmark_http` usó LiveServer Django, JWT y PostgreSQL temporal, 100 citas/consultas/imágenes; 1, 5 y 10 clientes, cinco requests por cliente, sin IA. Con 10 clientes/50 solicitudes: pacientes 4,45 req/s p50 2206 ms p95 2318; agenda 3,93 req/s 2353/2853; consultas 4,01 req/s 2413/2582; imágenes 3,92 req/s 2473/2745. Errores 0; máximo observado 12 conexiones a la DB de prueba, incluida la de monitorización. La ejecución coincidió con otras pruebas y latencias repetidamente ~2,2 s sugieren efectos del entorno/servidor de desarrollo no diagnosticados. Resultados **LOCAL HTTP BENCHMARK**, no capacidad, ni evidencia para recomendar PgBouncer. Repetir aisladamente con servidor de producción y sondas separadas antes de dimensionar. No se calcula p99 con 50 muestras.
