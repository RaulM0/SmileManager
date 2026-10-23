import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../../api/client";

export default function DiagnosticsPage() {
  const [params, setParams] = useSearchParams();
  const [data, setData] = useState(null);
  const [filters, setFilters] = useState({
    patient: params.get("patient") || "",
    type: params.get("type") || "",
    date: params.get("date") || "",
  });
  useEffect(() => {
    api(`diagnostics/?${params.toString()}`).then(setData);
  }, [params]);
  function submit(e) {
    e.preventDefault();
    setParams(
      Object.fromEntries(Object.entries(filters).filter(([, value]) => value)),
    );
  }
  return (
    <div className="container py-4">
      <h1 className="h2">Diagnósticos con IA</h1>
      <form onSubmit={submit} className="card border-0 shadow-sm my-4">
        <div className="card-body row g-3">
          <div className="col-md-4">
            <input
              aria-label="Paciente"
              className="form-control"
              placeholder="Nombre del paciente"
              value={filters.patient}
              onChange={(e) =>
                setFilters({ ...filters, patient: e.target.value })
              }
            />
          </div>
          <div className="col-md-3">
            <input
              aria-label="Tipo"
              className="form-control"
              placeholder="Tipo de imagen"
              value={filters.type}
              onChange={(e) => setFilters({ ...filters, type: e.target.value })}
            />
          </div>
          <div className="col-md-3">
            <input
              aria-label="Fecha"
              type="date"
              className="form-control"
              value={filters.date}
              onChange={(e) => setFilters({ ...filters, date: e.target.value })}
            />
          </div>
          <div className="col-md-2">
            <button className="btn btn-primary w-100">Filtrar</button>
          </div>
        </div>
      </form>
      {!data ? (
        <div className="page-loader">
          <div className="spinner-border text-primary" />
        </div>
      ) : (
        <>
          <div className="row g-3 mb-4">
            {[
              ["Total", data.statistics.total],
              ["Procesadas", data.statistics.processed],
              ["Pendientes", data.statistics.pending],
              ["Progreso", `${data.statistics.processed_percentage}%`],
            ].map(([label, value]) => (
              <div className="col-6 col-md-3" key={label}>
                <div className="card border-0 shadow-sm">
                  <div className="card-body">
                    <small className="text-muted">{label}</small>
                    <h2>{value}</h2>
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div className="row g-4">
            {data.results.map((image) => (
              <div className="col-md-6 col-lg-4" key={image.id}>
                <div className="card border-0 shadow-sm h-100">
                  <img
                    src={image.imagen_url}
                    className="clinical-thumbnail card-img-top"
                    alt={image.descripcion}
                  />
                  <div className="card-body">
                    <h2 className="h5">{image.patient_name}</h2>
                    <p>{image.tipo_imagen}</p>
                    <span
                      className={`badge bg-${image.resultados_url ? "success" : "warning"} mb-3`}
                    >
                      {image.resultados_url ? "Procesada" : "Pendiente"}
                    </span>
                    <Link
                      className="btn btn-primary d-block"
                      to={`/diagnostics/${image.id}`}
                    >
                      {image.resultados_url
                        ? "Ver / repetir análisis"
                        : "Analizar"}
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
