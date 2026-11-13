> Nota de arquitectura: esta medición es histórica. La inferencia y `benchmark_ai_synthetic.py` ahora viven en `../SmileIA`. SmileManager utiliza HTTP; estas cifras no incluyen su coste. Ver [operación de SmileIA](../operations/smileia.md).

# Perfil de IA

`DiagnosticosIA.services` construye `YOLO` una vez por proceso al importar; no por request. Predicción, archivos temporales, guardado y DB se realizan síncronamente. No hay historial de runs, hash de input/modelo, idempotencia o coordinación distribuida. GET de resultado no vuelve a analizar. La misma imagen/modelo podría reutilizarse solo tras definir validez clínica, trazabilidad y reanálisis explícito; no se añadió caché clínico.

**LOCAL BENCHMARK — NO PRODUCTION CAPACITY CLAIM:** `benchmark_ai_synthetic.py`, CPU, imagen blanca sintética de 320×320, sin DB, red ni S3. Construcción `YOLO` 74,5 ms (la inicialización puede ser diferida); primera predicción 372 ms de pared, con etapas reportadas por Ultralytics preprocess 13,68 ms, inferencia 196,28 ms, postprocess 4,24 ms. Dos llamadas concurrentes compartiendo modelo: 168 y 369 ms individuales, 380 ms de pared conjunta; muestra única y posible serialización interna. RSS antes 216,7 MB, pico observado 353,4 MB; CPU de proceso 3,828 s en el tramo medido, 7 threads PyTorch reportados. Se intentó limitar threads y el runtime reportó 7; no extrapolar. Upload y guardado de resultado no fueron cronometrados. No se probaron 5/10 inferencias ni p95 por seguridad de la máquina.

No hay evidencia para imponer un semáforo por proceso sin estudiar comportamiento multi-worker; throttle no controla concurrencia. **DISTRIBUTED COORDINATION REQUIRED** si se requiere una cuota global entre procesos/instancias. No se ha demostrado recuperación tras reinicios, ni timeout de inferencia. La operación real puede necesitar proceso aislado por disponibilidad/CPU.

**ASYNC PROCESSING RECOMMENDED** si se necesitan XLSX >1000, trabajos recuperables, reintentos o una inferencia que exceda SLA medido. Celery no se instaló; la prueba no demuestra que sea imprescindible ahora. Redis tampoco se instaló: podría ser broker o coordinación, pero elegirlo requiere necesidad y diseño operativo.

## Fase 3.1

Nueva ejecución sintética local, CPU, 320×320, 4 threads PyTorch: 1/2/5/10 llamadas tuvieron tiempos de pared 951/507/1496/3310 ms; latencias individuales aproximadas 949; 251–497; 308–1439; 405–3215 ms. Errores 0; CPU de proceso 4,25/2,59/7,55/14,53 s, RSS pico 295/331/431/569 MB. La primera incluye calentamiento. Se detiene si RSS supera 750 MB, memoria libre baja de 1,5 GB, una muestra tarda >5 s o el grupo >8 s. Muestras mínimas, bajo carga de otros procesos, sin HTTP ni storage: **LOCAL BENCHMARK**, no capacidad de producción.

**ESTIMATE:** multiplicar el pico de proceso 569 MB por 2/4 workers da aproximadamente 1,14/2,28 GB; no es benchmark multi-worker y compartir páginas del SO, imágenes reales y estado de memoria pueden cambiarlo. La aplicación ahora registra runs e idempotencia según [ciclo](../architecture/ai-analysis-lifecycle.md). Puede seguir síncrona para carga y SLA aún no definidos, sin durabilidad tras reinicio; **ASYNC PROCESSING RECOMMENDED** si se exige recuperación de trabajos o concurrencia sostenida. No se añadió Celery ni Redis.
