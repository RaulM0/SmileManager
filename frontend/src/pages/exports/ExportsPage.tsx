import { useApiDownload } from "../../hooks/useApiDownload";

const exports = [
  ["Pacientes", "Datos generales y contacto", "patients.xlsx", "bi-people"],
  [
    "Consultas",
    "Historial clínico",
    "consultations.xlsx",
    "bi-clipboard2-pulse",
  ],
  [
    "Imágenes clínicas",
    "Metadatos de imágenes",
    "clinical-images.xlsx",
    "bi-images",
  ],
];
export default function ExportsPage() {
  const { active, download } = useApiDownload();
  return (
    <div className="workspace-page co-mx-auto co-max-w-[1320px]">
      <div className="workspace-page-header">
        <div>
          <h1>Exportar datos</h1>
          <p className="clinical-page-description">
            Descarga archivos de trabajo en formato Excel
          </p>
        </div>
      </div>
      <div className="export-list">
        {exports.map(([title, text, path, icon]) => (
          <div className="export-row" key={path}>
            <i className={`bi ${icon} export-icon`} aria-hidden="true" />
            <div>
              <h2>{title}</h2>
              <p>{text}</p>
            </div>
            <a
              className="clinical-action-outline"
              href={`/api/v1/clinics/exports/${path}`}
              aria-disabled={Boolean(active)}
              onClick={(event) => {
                event.preventDefault();
                void download(path, `clinics/exports/${path}`, path);
              }}
            >
              {active === path ? "Preparando descarga…" : "Descargar Excel"}
            </a>
          </div>
        ))}
      </div>
    </div>
  );
}
