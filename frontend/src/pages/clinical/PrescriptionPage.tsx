import { Link, useParams } from "react-router-dom";
import { useResource } from "../../hooks/useResource";
import type { Consultation } from "../../types/domain";

export default function PrescriptionPage() {
  const { id } = useParams();
  const { data: item, error, reload } = useResource<Consultation>(`consultations/${id}/`);
  if (error)
    return <div className="workspace-page co-mx-auto co-max-w-[1320px]"><div className="workspace-inline-error" role="alert">{error}</div><button className="clinical-action-outline co-mt-3" onClick={reload}>Reintentar</button></div>;
  if (!item)
    return (
      <div className="page-loader" role="status" aria-label="Cargando receta">
        <div className="workspace-loader-spinner" />
      </div>
    );
  return (
    <div className="workspace-page co-mx-auto co-max-w-[1320px]">
      <div className="prescription-context">Consulta #{item.id}</div>
      <article className="prescription-sheet">
          <h1>Receta médica</h1>
          <div className="prescription-patient">
          <p>
            <strong>Paciente:</strong> {item.paciente.full_name}
          </p>
          <p>
            <strong>Fecha:</strong>{" "}
            {new Date(item.fecha_consulta).toLocaleString("es-MX")}
          </p>
          </div>
          <h2>Diagnóstico</h2>
          <p>{item.diagnostico}</p>
          <h2>Tratamiento</h2>
          <p>{item.tratamiento}</p>
          <h2>Observaciones</h2>
          <p>{item.observaciones}</p>
      </article>
      <div className="co-flex co-flex-wrap co-gap-3 co-mt-4 print-hidden">
        <Link className="clinical-action-outline" to={`/patients/${item.paciente.id}`}>Ver paciente</Link>
        <Link className="clinical-action-outline" to={`/patients/${item.paciente.id}/consultations`}>Historial de consultas</Link>
      </div>
      <button
        className="clinical-action-primary co-mt-4 print-hidden"
        type="button"
        onClick={() => window.print()}
      >
        <i className="bi bi-printer" aria-hidden="true" />
        Descargar PDF / Imprimir
      </button>
    </div>
  );
}
