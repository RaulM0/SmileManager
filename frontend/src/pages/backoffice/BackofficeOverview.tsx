import { Link } from "react-router-dom";
import { Load, Events } from "./shared";
import { useAdmin } from "./useAdmin";
import type { Dashboard, System } from "./types";

export function BackofficeDashboard() {
  const query = useAdmin<Dashboard>("dashboard/");
  const d = query.data;
  return (
    <>
      <div className="workspace-page-header">
        <div>
          <h1>Resumen del sistema</h1>
          <p className="clinical-page-description">
            Actividad operativa y acceso de usuarios
          </p>
        </div>
      </div>
      <Load pending={query.isPending} error={query.error}>
        {d && (
          <>
            <div
              className="workspace-summary-strip backoffice-summary-strip"
              aria-label="Resumen operativo"
            >
              {[
                ["Usuarios activos", d.users.active],
                ["Usuarios inactivos", d.users.inactive],
                ["Pacientes activos", d.patients_active ?? "—"],
                ["Citas hoy", d.appointments?.today ?? "—"],
                ["Próximas citas", d.appointments?.upcoming ?? "—"],
                ...(d.ai ? [["IA en curso", d.ai.running], ["IA fallida", d.ai.failed], ["IA posiblemente detenida", d.ai.stale]] : []),
              ].map(([label, count]) => (
                <div key={label}>
                  <span>{label}</span>
                  <strong>{count}</strong>
                </div>
              ))}
            </div>
            <section className="workspace-section">
              <div className="workspace-section-heading">
                <div>
                  <h2>Actividad administrativa reciente</h2>
                  <p>Últimos cambios de acceso</p>
                </div>
                <Link to="/backoffice/audit">
                  Ver auditoría{" "}
                  <i className="bi bi-arrow-right" aria-hidden="true" />
                </Link>
              </div>
              {d.recent_admin_events.length ? (
                <Events events={d.recent_admin_events} />
              ) : (
                <div className="workspace-empty-state">
                  <span>Aún no hay acciones administrativas.</span>
                </div>
              )}
            </section>
          </>
        )}
      </Load>
    </>
  );
}

export function BackofficeSystem() {
  const q = useAdmin<System>("system/");
  return (
    <>
      <div className="workspace-page-header">
        <div>
          <h1>Estado del sistema</h1>
          <p className="clinical-page-description">
            Disponibilidad de los servicios de SmileManager.
          </p>
        </div>
      </div>
      <Load pending={q.isPending} error={q.error}>
        {q.data && (
          <dl className="clinical-form-surface admin-detail-grid">
            <div>
              <dt>Aplicación</dt>
              <dd>
                {q.data.application === "ok" ? "Disponible" : "No disponible"}
              </dd>
            </div>
            <div>
              <dt>Base de datos</dt>
              <dd>
                {q.data.database === "ok" ? "Disponible" : "No disponible"}
              </dd>
            </div>
            <div>
              <dt>Modelo de IA</dt>
              <dd>No comprobado en esta consulta</dd>
            </div>
          </dl>
        )}
      </Load>
    </>
  );
}
