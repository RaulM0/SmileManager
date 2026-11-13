import { Link, useParams } from "react-router-dom";
import { formatDate } from "../../utils/date";
import { useResource } from "../../hooks/useResource";
import type { Appointment } from "../../types/domain";
import { appointmentStatus } from "../../utils/appointmentStatus";

export default function AppointmentDetailPage() {
  const { id } = useParams();
  const {
    data: item,
    error,
    reload,
  } = useResource<Appointment>(`clinics/appointments/${id}/`);
  if (error)
    return (
      <div className="workspace-page co-mx-auto co-max-w-[1320px]">
        <div className="workspace-inline-error" role="alert">
          {error}
        </div>
        <button className="clinical-action-outline co-mt-3" onClick={reload}>
          Reintentar
        </button>
      </div>
    );
  if (!item)
    return (
      <div className="page-loader" role="status" aria-label="Cargando cita">
        <div className="workspace-loader-spinner" />
      </div>
    );
  return (
    <div className="workspace-page co-mx-auto co-max-w-[1320px]">
      <div className="workspace-page-header">
        <div>
          <h1>Detalle de cita #{item.id}</h1>
          <p className="clinical-page-description">{item.paciente.full_name}</p>
        </div>
        <Link
          className="clinical-action-primary"
          to={`/appointments/${id}/edit`}
        >
          Editar
        </Link>
      </div>
      <div className="workspace-section">
        <div className="workspace-section-heading">
          <div>
            <h2>Información de la cita</h2>
            <p>Horario y datos de atención</p>
          </div>
          <span
            className={`appointment-status ${appointmentStatus[item.estatus]?.className || ""}`}
          >
            {appointmentStatus[item.estatus]?.label || item.estatus_display}
          </span>
        </div>
        <dl className="patient-summary-list appointment-detail-list">
          <div>
            <dt>Paciente</dt>
            <dd>
              <Link to={`/patients/${item.paciente.id}`}>
                {item.paciente.full_name}
              </Link>
            </dd>
          </div>
          <div>
            <dt>Fecha y hora</dt>
            <dd>
              <time dateTime={`${item.fecha}T${item.hora}`}>
                {formatDate(item.fecha)} · {item.hora.slice(0, 5)}
              </time>
            </dd>
          </div>
          <div>
            <dt>Motivo</dt>
            <dd>{item.motivo}</dd>
          </div>
          <div className="appointment-observations">
            <dt>Observaciones</dt>
            <dd>{item.observaciones || "—"}</dd>
          </div>
        </dl>
      </div>
    </div>
  );
}
