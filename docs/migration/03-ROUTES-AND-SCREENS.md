# Rutas y pantallas legacy

| Prefijo               | Pantallas/operaciones                                                                                                             |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `/sesiones/`          | login, logout                                                                                                                     |
| `/home/`              | dashboard, privacidad                                                                                                             |
| `/registroPacientes/` | hub, CRUD lógico de pacientes, expediente, consultas, recetas, imágenes, Excel, email, odontograma, estudios, PDF, consentimiento |
| `/menu_citas/`        | calendario, alta, búsqueda, edición, estados y detalle                                                                            |
| `/diagnosticos/`      | filtros, estadísticas y análisis YOLO                                                                                             |
| `/admin/`             | administración Django                                                                                                             |

La relación detallada ruta→view→template→React está en los inventarios `02`, `06` y `07`. Se conservarán estas rutas durante la comprobación de paridad. React se montará inicialmente en `/app/` y la API en `/api/v1/` para evitar colisiones.ok,
