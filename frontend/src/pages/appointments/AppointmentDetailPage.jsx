import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../../api/client";

export default function AppointmentDetailPage() {
  const { id } = useParams();
  const [item, setItem] = useState(null);
  useEffect(() => {
    api(`appointments/${id}/`).then(setItem);
  }, [id]);
  if (!item)
    return (
      <div className="page-loader">
        <div className="spinner-border text-primary" />
      </div>
    );
  return (
    <div className="container py-4">
      <div className="d-flex justify-content-between">
        <h1 className="h2">Detalle de cita #{item.id}</h1>
        <Link className="btn btn-primary" to={`/appointments/${id}/edit`}>
          Editar
        </Link>
      </div>
      <div className="card border-0 shadow-sm mt-4">
        <div className="card-body p-4">
          <dl className="row">
            <dt className="col-sm-3">Paciente</dt>
            <dd className="col-sm-9">{item.paciente.full_name}</dd>
            <dt className="col-sm-3">Fecha y hora</dt>
            <dd className="col-sm-9">
              {item.fecha} · {item.hora.slice(0, 5)}
            </dd>
            <dt className="col-sm-3">Estado</dt>
            <dd className="col-sm-9">{item.estatus_display}</dd>
            <dt className="col-sm-3">Motivo</dt>
            <dd className="col-sm-9">{item.motivo}</dd>
            <dt className="col-sm-3">Observaciones</dt>
            <dd className="col-sm-9">{item.observaciones}</dd>
          </dl>
        </div>
      </div>
    </div>
  );
}
