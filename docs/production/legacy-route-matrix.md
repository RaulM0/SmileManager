# Estado de las rutas HTML retiradas

Todas las rutas de las antiguas aplicaciones Django bajo `/sesiones/`, `/home/`, `/registroPacientes/`, `/menu_citas/`, `/diagnosticos/` y `/admin/` están retiradas. No se realiza redirección automática para operaciones con datos clínicos; devuelven 404. Ver [legacy-routes.md](legacy-routes.md) para el alcance y la compatibilidad restante.

La SPA está bajo `/app/`, los servicios bajo `/api/v1/` y las comprobaciones de salud bajo `/health/`. Los inventarios en `docs/migration/` describen el estado histórico previo al retiro.
