# PostgreSQL: planes e índices

**LOCAL BENCHMARK — NO PRODUCTION CAPACITY CLAIM.** Con 1000 pacientes y una cita sintética por paciente, `EXPLAIN ANALYZE BUFFERS` de búsqueda por médico y `nombre__icontains` usó Index Scan del FK de médico, seguido de filtro `upper(nombre) LIKE '%SYNTHETIC%'`; tiempo de ejecución 0,697 ms antes y 0,820 ms después en muestras separadas. No es el OR completo del endpoint ni demuestra eficiencia de substring a gran escala.

La consulta sintética de próximas citas usó Sort (quicksort, 118 kB) sobre Nested Loop: Index Scan de médico y Bitmap Index Scan por paciente, 1000 loops, 3018 buffers, ~4,05 ms antes y ~3,93 ms después. Estimó 2 filas y obtuvo 1000 en datos recién insertados; analizar estadísticas y distribución real antes de inferir un índice compuesto. El benchmark no prueba escrituras ni mantenimiento de índices.

**No se añadió índice ni migración:** los planes pequeños no demuestran beneficio que compense escritura y almacenamiento. Evaluar EXPLAIN con datos sintéticos representativos y estadísticas actualizadas; explorar índice de fecha/paciente o búsqueda trigram solo si mediciones lo justifican. PageNumber/offset sigue siendo suficiente para la lista de pacientes medida; no se introdujo cursor ni Elasticsearch.
