import { Link, useParams } from "react-router-dom";
import { useResource } from "../../hooks/useResource";
import type { Consultation, Paginated } from "../../types/domain";

const actions = [
  ["Antecedentes médicos", "Condiciones y datos relevantes para la atención", "bi-heart-pulse", "medical-history"],
  ["Nueva consulta", "Registrar motivo, diagnóstico y tratamiento", "bi-clipboard2-plus", "consultations/new"],
  ["Historial de consultas", "Revisar la evolución registrada", "bi-clock-history", "consultations"],
  ["Odontograma", "Explorar y actualizar piezas dentales", "bi-grid-3x3-gap", "odontogram"],
  ["Imágenes clínicas", "Consultar estudios asociados a consultas", "bi-images", "images"],
  ["Progreso", "Estudio clínico comparativo", "bi-arrow-left-right", "comparative-study"],
  ["Consentimiento", "Revisar autorización y documento asociado", "bi-file-earmark-check", "consent"],
];

export default function ClinicalRecordPage() {
  const { id } = useParams();
  const { data, error, reload } = useResource<Paginated<Consultation>>(`patients/${id}/consultations/`);
  const consultations = data?.results;
  return (
    <div className="workspace-page co-mx-auto co-max-w-[1320px]">
      <div className="workspace-page-header">
        <div>
          <h1>Resumen clínico</h1>
          <p className="clinical-page-description">Acceso a la información y tareas clínicas del paciente</p>
        </div>
      </div>
      <div className="patient-task-list" aria-label="Secciones clínicas">
        {actions.map(([title, description, icon, path]) => (
          <Link className="clinical-task-row" to={`/patients/${id}/${path}`} key={path}>
            <i className={`bi ${icon} patient-task-icon`} aria-hidden="true" />
            <span><strong>{title}</strong><small>{description}</small></span>
            <i className="bi bi-chevron-right clinical-task-arrow" aria-hidden="true" />
          </Link>
        ))}
      </div>
      <section className="workspace-section co-mt-5" aria-labelledby="recent-consultations">
        <div className="workspace-section-heading"><h2 id="recent-consultations">Últimas consultas</h2><Link to={`/patients/${id}/consultations`}>Ver historial</Link></div>
        {error ? <div className="workspace-inline-error" role="alert">No se pudieron cargar las consultas. <button type="button" className="clinical-action-outline clinical-action-compact" onClick={reload}>Reintentar</button></div> : !consultations ? <p role="status">Cargando consultas…</p> : consultations.length ? <div className="clinical-timeline"><ol aria-label="Últimas consultas registradas">{consultations.slice(0, 3).map((item) => <li className="clinical-timeline-entry" key={item.id}><time className="clinical-timeline-date" dateTime={item.fecha_consulta}>{new Date(item.fecha_consulta).toLocaleDateString("es-MX")}</time><span>{item.motivo_consulta}</span><Link to={`/consultations/${item.id}/prescription`}>Ver receta</Link></li>)}</ol></div> : <p>No hay consultas registradas. <Link to={`/patients/${id}/consultations/new`}>Registrar consulta</Link></p>}
      </section>
    </div>
  );
}
