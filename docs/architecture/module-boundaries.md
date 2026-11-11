# Límites de módulos

SmileManager mantiene un monolito Django/DRF con una interfaz React. Los módulos de dominio pueden utilizar el ORM y las excepciones de DRF existentes, pero no importan endpoints ni servicios de `api`. Los comandos de administración son adaptadores de entrada y quedan fuera de esa restricción.

## Backend

- `Usuarios/clinic_context.py`: membresías, capacidades y orden de bloqueo para operaciones por clínica.
- `Usuarios/permissions.py`: asignaciones administrativas explícitas del producto.
- `Usuarios/audit_integrity.py`: huellas, sellos y verificación de eventos.
- `Pacientes/access.py`: alcance por profesional, clínica y coherencia de recursos clínicos, incluyendo la frontera histórica.
- `api/permissions.py`: adaptación de permisos administrativos a DRF.
- `api/clinic_context.py`: contexto HTTP compartido y registro de auditoría para endpoints clínicos.
- `api/pagination.py`: contratos de paginación compartidos.
- `api/auth_views.py`: sesión, login, renovación y logout.
- `api/legacy_views.py`: contratos clínicos históricos; solo se importan al montar `legacy_urls` con `LEGACY_CLINICAL_API_ENABLED`.
- `api/services/`: casos de uso existentes consumidos por los adaptadores HTTP. Esta reorganización no mueve todos los servicios ni pretende eliminar toda dependencia de Django/DRF.

Los endpoints actuales no deben importar infraestructura desde endpoints de otro recurso. Las políticas clínicas mantienen la comprobación de membresía vigente y asignación profesional; las escrituras conservan las transacciones y el orden de bloqueos anteriores.

## Frontend

`api/client.ts` se ocupa del transporte, autenticación, cabecera de clínica, cancelación y respuestas. Envía exactamente la ruta recibida. Los servicios, pantallas y recursos protegidos usan explícitamente las rutas `clinics/`; no existe traducción automática ni retorno a rutas históricas cuando falta una clínica.

Las claves de React Query incluyen clínica, tipo de recurso y ruta. Los cambios de clínica y sesión siguen limpiando las consultas y cancelando solicitudes. Al invalidar por prefijo de ruta, hay que respetar los tres elementos de la clave.

El backoffice se divide en navegación, resumen, usuarios, auditoría y ejecuciones IA, con tipos, consultas y componentes compartidos. `Backoffice.tsx` solo reexporta componentes para conservar los imports de navegación y pruebas.

## Motor de IA

`DiagnosticosIA/services.py` importa Ultralytics y carga el modelo al primer análisis. Un bloqueo evita inicializaciones duplicadas y otro serializa el acceso al predictor mutable. Si la carga falla, una solicitud posterior puede reintentarla. El artefacto del modelo debe permanecer inmutable durante la vida del proceso.

La inferencia sigue siendo síncrona y consume un trabajador HTTP mientras se ejecuta. El ciclo existente conserva idempotencia, inferencia fuera de bloqueos de base y autorización antes de publicar el resultado. Una cola duradera con trabajadores separados requeriría definir entrega, recuperación y operación; no forma parte de esta reorganización.

## Validación y operación

`api/tests/test_architecture_boundaries.py` verifica la dirección de dependencias de los módulos de dominio, la importación de IA sin cargar Torch/Ultralytics y la inicialización concurrente y recuperable del modelo. Las pruebas de servicios del frontend verifican rutas explícitas con y sin clínica seleccionada.

No hay cambios de esquema ni migraciones de datos. Para ejecutar la suite dentro del contenedor de desarrollo, vaciar `THROTTLE_REDIS_URL` en ese proceso evita heredar el limitador compartido de desarrollo; las pruebas de Redis utilizan su conexión aislada `RATE_LIMIT_TEST_REDIS_URL`.

Al desplegar, reiniciar todos los procesos Django para cargar los módulos nuevos y publicar el frontend compilado junto al backend. Para revertir, restaurar ambas versiones y reiniciar los procesos; no se requiere revertir la base de datos.
