import { Link } from "react-router-dom";

const actions = [
  [
    "Todos los pacientes",
    "Consultar registros",
    "bi-people-fill",
    "/patients/list",
  ],
  [
    "Registrar paciente",
    "Crear un expediente",
    "bi-person-plus-fill",
    "/patients/new",
  ],
  ["Buscar pacientes", "Filtros y paginación", "bi-search", "/patients/search"],
  [
    "Historial médico",
    "Seleccionar expediente",
    "bi-clipboard2-pulse",
    "/clinical-record",
  ],
  [
    "Exportar datos",
    "Descargar archivos Excel",
    "bi-file-earmark-spreadsheet",
    "/exports",
  ],
  [
    "Contactar pacientes",
    "Enviar correo electrónico",
    "bi-envelope",
    "/patients/contact",
  ],
];
export default function PatientsHubPage() {
  return (
    <div className="workspace-page co-mx-auto co-max-w-[1320px]">
      <div className="workspace-page-header">
        <div>
          <h1>Gestión de pacientes</h1>
          <p className="clinical-page-description">
            Acceso a expedientes y tareas de atención
          </p>
        </div>
        <Link className="clinical-action-primary" to="/patients/new">
          <i className="bi bi-person-plus" aria-hidden="true" />
          Registrar paciente
        </Link>
      </div>
      <div className="patient-task-list">
        {actions.map(([title, text, icon, to]) => (
          <div className="patient-task-row" key={title}>
            <i className={`bi ${icon} patient-task-icon`} aria-hidden="true" />
            <div>
              <h2>{title}</h2>
              <p>{text}</p>
            </div>
            <Link
              className="clinical-action-outline clinical-action-compact"
              aria-label={`Acceder a ${title}`}
              to={to}
            >
              Acceder
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}
