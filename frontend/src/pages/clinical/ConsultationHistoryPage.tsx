import { Link, useParams } from "react-router-dom";
import { useState } from "react";
import { useResource } from "../../hooks/useResource";
import type { Consultation, Paginated } from "../../types/domain";

const consultationDateFormat = new Intl.DateTimeFormat("es-MX", {
  day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit", hour12: false,
});
function formatConsultationDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value) : consultationDateFormat.format(date);
}

export default function ConsultationHistoryPage() {
  const { id } = useParams();
  const [page, setPage] = useState(1);
  const { data, error, reload } = useResource<Paginated<Consultation>>(`patients/${id}/consultations/?page=${page}`);
  const items = data?.results;
  return (
    <div className="workspace-page co-mx-auto co-max-w-[1320px]">
      <div className="workspace-page-header">
        <div><h1>Historial de consultas</h1></div>
        <Link
          to={`/patients/${id}/consultations/new`}
          className="clinical-action-primary"
        >
          Nueva consulta
        </Link>
      </div>
      {error && <div className="workspace-inline-error" role="alert">{error}<button className="clinical-action-outline co-ml-3" onClick={reload}>Reintentar</button></div>}
      {!items ? (error ? null : <div className="page-loader" role="status" aria-label="Cargando consultas">
          <div className="workspace-loader-spinner" />
        </div>) : (
        <div className="clinical-timeline">
          {items.length ? <ol aria-label="Consultas registradas para este paciente">
            {items.map((item) => (
              <li className="clinical-timeline-entry" key={item.id}>
                <div className="clinical-timeline-date"><time dateTime={item.fecha_consulta}>{formatConsultationDate(item.fecha_consulta)}</time></div>
                <div className="clinical-timeline-content">
                  <h2>{item.motivo_consulta}</h2>
                  <p><strong>Diagnóstico:</strong> {item.diagnostico}</p>
                </div>
                <Link className="clinical-action-outline clinical-action-compact" to={`/consultations/${item.id}/prescription`} aria-label={`Ver receta de la consulta del ${formatConsultationDate(item.fecha_consulta)}`}>Ver receta</Link>
              </li>
            ))}
          </ol> : <div className="workspace-empty-state">No hay consultas registradas.</div>}
        </div>
      )}
      {data && <nav aria-label="Páginas de consultas"><button disabled={page === 1} onClick={() => setPage(page - 1)}>Anterior</button><span> Página {page} </span><button disabled={!data.next} onClick={() => setPage(page + 1)}>Siguiente</button></nav>}
    </div>
  );
}
