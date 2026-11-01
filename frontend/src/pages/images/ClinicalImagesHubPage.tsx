import { Link, useParams } from "react-router-dom";

const actions = [
  ["Cargar imagen", "Añadir un estudio a una consulta del expediente", "bi-cloud-arrow-up", "upload"],
  ["Buscar imágenes", "Filtrar por fecha o consulta", "bi-search", "search"],
  ["Historial", "Revisar, descargar o eliminar estudios guardados", "bi-clock-history", "history"],
];

export default function ClinicalImagesHubPage() {
  const { id } = useParams();
  return (
    <div className="workspace-page co-mx-auto co-max-w-[1320px]">
      <div className="workspace-page-header"><div><h1>Imágenes clínicas</h1></div></div>
      <div className="patient-task-list">
        {actions.map(([title, description, icon, path]) => (
          <Link className="clinical-task-row" to={`/patients/${id}/images/${path}`} key={path}>
            <i className={`bi ${icon} patient-task-icon`} aria-hidden="true" />
            <span><h2>{title}</h2><small>{description}</small></span>
            <i className="bi bi-chevron-right clinical-task-arrow" aria-hidden="true" />
          </Link>
        ))}
      </div>
    </div>
  );
}
