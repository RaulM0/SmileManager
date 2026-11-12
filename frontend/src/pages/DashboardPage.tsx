import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { formatDate } from "../utils/date";
import { useResource } from "../hooks/useResource";
import type { Appointment, Dashboard } from "../types/domain";
import { appointmentStatus } from "../utils/appointmentStatus";

function AppointmentTable({
  appointments,
  future = false,
}: {
  appointments: Appointment[];
  future?: boolean;
}) {
  if (!appointments.length)
    return (
      <div className="workspace-empty-state">
        <i className="bi bi-calendar-x" aria-hidden="true" />
        <span>No hay {future ? "próximas " : ""}citas</span>
      </div>
    );
  return (
    <div className="workspace-table-scroll">
      <p className="table-scroll-hint">
        <i className="bi bi-arrow-left-right" aria-hidden="true" />
        Desliza la tabla para ver todas las columnas
      </p>
      <table className="workspace-data-table">
        <caption className="co-sr-only">
          {future ? "Próximas citas" : "Citas de hoy"}
        </caption>
        <thead>
          <tr>
            {future && <th>Fecha</th>}
            <th>Hora</th>
            <th>Paciente</th>
            <th>Motivo</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody>
          {appointments.map((item) => (
            <tr key={item.id}>
              {future && (
                <td data-label="Fecha">
                  <time dateTime={item.fecha}>{formatDate(item.fecha)}</time>
                </td>
              )}
              <td data-label="Hora">
                <Link to={`/appointments/${item.id}`}>
                  <time className="time-value">{item.hora.slice(0, 5)}</time>
                </Link>
              </td>
              <td data-label="Paciente">
                {item.paciente.nombre} {item.paciente.appat}
              </td>
              <td data-label="Motivo">{item.motivo}</td>
              <td data-label="Estado">
                <span
                  className={`appointment-status ${appointmentStatus[item.estatus]?.className || ""}`}
                >
                  {appointmentStatus[item.estatus]?.label || item.estatus}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  const { data, error, reload } = useResource<Dashboard>("clinics/dashboard/");
  if (error)
    return (
      <div className="workspace-page">
        <div className="workspace-inline-error" role="alert">
          {error}
        </div>
        <button className="clinical-action-outline co-mt-3" onClick={reload}>
          Reintentar
        </button>
      </div>
    );
  if (!data)
    return (
      <div className="page-loader">
        <div className="workspace-loader-spinner" />
      </div>
    );
  return (
    <div className="workspace-page co-mx-auto co-max-w-[1560px]">
      <div className="workspace-page-header">
        <div>
          <h1>
            Bienvenido,{" "}
            {user && (
              <span className="co-text-clinical-brand">
                Dr. {user.username.toUpperCase()}
              </span>
            )}
          </h1>
          <p className="clinical-page-description">
            Agenda y actividad clínica
          </p>
        </div>
        <Link to="/appointments" className="clinical-action-primary">
          <i className="bi bi-calendar3" aria-hidden="true" />
          Abrir agenda
        </Link>
      </div>
      <div className="workspace-summary-strip" aria-label="Resumen operativo">
        <div>
          <span>Pacientes registrados</span>
          <strong>{data.patient_count}</strong>
          <Link to="/patients">Ver pacientes</Link>
        </div>
        <div>
          <span>Citas de hoy</span>
          <strong>{data.today_count ?? data.today.length}</strong>
          <span className="co-text-clinical-muted">Agenda del día</span>
        </div>
      </div>
      <section className="workspace-section" aria-labelledby="today-heading">
        <div className="workspace-section-heading">
          <div>
            <h2 id="today-heading">Agenda de hoy</h2>
            <p>Citas programadas para la jornada</p>
          </div>
          <Link to="/appointments">
            Ver agenda completa{" "}
            <i className="bi bi-arrow-right" aria-hidden="true" />
          </Link>
        </div>
        <AppointmentTable appointments={data.today} />
        {data.today_count > data.today.length && (
          <p className="workspace-section-note">
            Se muestran {data.today.length} de {data.today_count} citas.{" "}
            <Link to="/appointments">Ver agenda completa</Link>
          </p>
        )}
      </section>
      <section className="workspace-section" aria-labelledby="upcoming-heading">
        <div className="workspace-section-heading">
          <div>
            <h2 id="upcoming-heading">Próximas citas</h2>
            <p>Siguientes pacientes programados</p>
          </div>
        </div>
        <AppointmentTable appointments={data.upcoming} future />
        {data.upcoming.length > 0 && (
          <p className="workspace-section-note">
            Estas son tus próximas citas.{" "}
            <Link to="/appointments">
              Ver agenda completa{" "}
              <i className="bi bi-arrow-right" aria-hidden="true" />
            </Link>
          </p>
        )}
      </section>
    </div>
  );
}
