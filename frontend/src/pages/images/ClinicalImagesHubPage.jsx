import { Link, useParams } from "react-router-dom";
export default function ClinicalImagesHubPage() {
  const { id } = useParams();
  return (
    <div className="container py-4">
      <h1 className="h2 mb-4">Imágenes clínicas</h1>
      <div className="row g-4">
        <div className="col-md-4">
          <Link
            className="card border-0 shadow-sm text-decoration-none h-100"
            to={`/patients/${id}/images/upload`}
          >
            <div className="card-body p-4">
              <i className="bi bi-cloud-arrow-up fs-2" />
              <h2 className="h5 mt-3">Cargar imagen</h2>
            </div>
          </Link>
        </div>
        <div className="col-md-4">
          <Link
            className="card border-0 shadow-sm text-decoration-none h-100"
            to={`/patients/${id}/images/search`}
          >
            <div className="card-body p-4">
              <i className="bi bi-search fs-2" />
              <h2 className="h5 mt-3">Buscar imágenes</h2>
            </div>
          </Link>
        </div>
        <div className="col-md-4">
          <Link
            className="card border-0 shadow-sm text-decoration-none h-100"
            to={`/patients/${id}/images/history`}
          >
            <div className="card-body p-4">
              <i className="bi bi-clock-history fs-2" />
              <h2 className="h5 mt-3">Historial</h2>
            </div>
          </Link>
        </div>
      </div>
    </div>
  );
}
