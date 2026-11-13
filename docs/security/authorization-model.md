# Modelo de autorización: inventario y política

## Inventario previo

No existe rol clínico formal en los modelos o rutas revisadas. `User.is_staff` y permisos/grupos del admin controlan Django admin; no equivalen a un rol clínico. La autoridad existente es `Paciente.medico`. El usuario activo autenticado propietario puede realizar las siguientes acciones sobre sus propios recursos; los ajenos deben responder 404.

| Recurso        | Acciones existentes                              | Control anterior                              | Riesgo                                                   |
| -------------- | ------------------------------------------------ | --------------------------------------------- | -------------------------------------------------------- |
| Paciente       | lista, búsqueda, crear, leer, editar, desactivar | médico del paciente                           | Sin permisos funcionales diferenciados.                  |
| Cita           | listar, crear, leer, editar, completar, cancelar | médico del paciente                           | Sin rol ni reglas de agenda por función.                 |
| Antecedentes   | leer, editar                                     | paciente propietario, lectura de primera fila | Fila histórica de otro médico puede quedar accesible.    |
| Consulta       | lista, crear, detalle, receta                    | combinación de paciente y médico según ruta   | Relaciones inconsistentes pueden diferir por superficie. |
| Odontograma    | leer, guardar                                    | paciente/médico                               | HTML y API tienen filtros distintos.                     |
| Imagen / IA    | lista, cargar, leer, archivo, borrar, analizar   | combinación de paciente/médico según ruta     | Relación inconsistente y salida de archivos.             |
| Estudio        | leer, crear, editar, PDF, archivos               | paciente y/o médico según ruta                | Selección de filas ajenas inconsistentes.                |
| Consentimiento | leer, aceptar, descargar                         | paciente y médico                             | Sin distinción de función clínica.                       |
| Exportaciones  | pacientes, consultas e imágenes                  | médico del paciente                           | Relaciones clínicas inconsistentes; descarga masiva.     |
| Correo         | enviar a paciente                                | paciente propietario                          | Todos los propietarios tienen misma capacidad.           |
| Administración | Django admin                                     | permisos Django de staff/grupos               | Acceso global debe gestionarse por separado.             |

## Política implementada

`api.policies.scoped` aplica propietario activo por paciente y para cada registro clínico también exige que su médico sea el propietario. En imágenes vinculadas exige además misma consulta, paciente y médico. Citas heredan autoridad del paciente. `owned_or_404` oculta objetos ajenos; `consistent_or_404` rechaza expedientes con filas inconsistentes en recursos de una sola ficha, en vez de reasignarlas. Es una regla de transición conservadora, no una política de transferencia: casos históricos requieren revisión. La API y rutas HTML usan la política en los puntos migrados; los administradores Django conservan permisos independientes y requieren revisión. Los servicios compartidos de exportación solo incluyen filas autorizadas. No existen permisos funcionales diferenciados y no se demuestra que nuevas vistas usen la política automáticamente.

La colaboración clínica entre profesionales, recepcionistas, asistentes y administradores clínicos es **BUSINESS DECISION REQUIRED**. Modelo futuro conceptual `User → Membership → Clinic → Role → Resource`; requiere decidir múltiples clínicas por usuario, acceso compartido, sucursales y transferencias antes de crear modelos o migrar datos. No se implementa tenant ni RBAC de negocio.
