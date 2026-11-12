import { useState } from "react";
import type { FormEvent } from "react";
import {
  Link,
  Navigate,
  useOutletContext,
  useSearchParams,
} from "react-router-dom";
import type { ClinicOption } from "../../layouts/ClinicWorkspace";
import {
  keepPreviousData,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import type { DiagnosticsPageData } from "../../types/domain";
import { ProtectedThumbnail } from "../../components/images/ProtectedImage";
import { diagnosticsService } from "../../services/diagnostics";
import { queryKeys } from "../../query/keys";
import { latestCachedData } from "../../query/latestCachedData";

export default function DiagnosticsPage() {
  const outlet = useOutletContext<{ activeClinic?: ClinicOption } | null>();
  const activeClinic = outlet?.activeClinic;
  const queryClient = useQueryClient();
  const [params, setParams] = useSearchParams();
  const [filters, setFilters] = useState({
    patient: params.get("patient") || "",
    type: params.get("type") || "",
    date: params.get("date") || "",
  });
  const listing = useQuery({
    queryKey: queryKeys.diagnosticList(params.toString()),
    queryFn: () => diagnosticsService.list(params.toString()),
    placeholderData: keepPreviousData,
    enabled: activeClinic?.ai_effective !== false,
  });
  const data: DiagnosticsPageData | undefined =
    listing.data ??
    latestCachedData<DiagnosticsPageData>(queryClient, [
      ...queryKeys.diagnostics,
      "list",
    ]);
  const error = listing.error?.message ?? "";
  function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setParams(
      Object.fromEntries(Object.entries(filters).filter(([, value]) => value)),
    );
  }
  if (activeClinic?.ai_effective === false) return <Navigate to="/" replace />;
  return (
    <div className="workspace-page co-mx-auto co-max-w-[1560px]">
      <div className="workspace-page-header">
        <div>
          <h1>Diagnósticos con IA</h1>
          <p className="clinical-page-description">
            Revisa resultados y procesa estudios pendientes
          </p>
        </div>
      </div>
      <form
        onSubmit={submit}
        className="clinical-filter-surface"
        aria-label="Filtros de diagnóstico"
      >
        <div className="clinical-filter-grid">
          <div className="clinical-filter-col-4">
            <label htmlFor="diagnostic-patient" className="clinical-form-label">
              Paciente
            </label>
            <input
              id="diagnostic-patient"
              aria-label="Paciente"
              className="clinical-form-control"
              placeholder="Nombre del paciente"
              value={filters.patient}
              onChange={(e) =>
                setFilters({ ...filters, patient: e.target.value })
              }
            />
          </div>
          <div className="clinical-filter-col-3">
            <label htmlFor="diagnostic-type" className="clinical-form-label">
              Tipo de imagen
            </label>
            <input
              id="diagnostic-type"
              aria-label="Tipo"
              className="clinical-form-control"
              placeholder="Tipo de imagen"
              value={filters.type}
              onChange={(e) => setFilters({ ...filters, type: e.target.value })}
            />
          </div>
          <div className="clinical-filter-col-3">
            <label htmlFor="diagnostic-date" className="clinical-form-label">
              Fecha
            </label>
            <input
              id="diagnostic-date"
              aria-label="Fecha"
              type="date"
              className="clinical-form-control"
              value={filters.date}
              onChange={(e) => setFilters({ ...filters, date: e.target.value })}
            />
          </div>
          <div className="clinical-filter-col-2 co-flex co-items-end">
            <button className="clinical-action-primary co-w-full">
              Filtrar
            </button>
          </div>
        </div>
      </form>
      {error && (
        <div
          className={
            data
              ? "workspace-inline-warning co-mb-4"
              : "workspace-inline-error co-mb-4"
          }
          role="alert"
        >
          {error}
          {data && <span> Se muestran los resultados de la última carga.</span>}
          <button
            className="clinical-action-outline co-ml-3"
            onClick={() => void listing.refetch()}
          >
            Reintentar
          </button>
        </div>
      )}
      {listing.isFetching && data && (
        <p className="clinical-loading-note" role="status">
          Actualizando diagnósticos…
        </p>
      )}
      {!data ? (
        error ? null : (
          <div
            className="page-loader"
            role="status"
            aria-label="Cargando diagnósticos"
          >
            <div className="workspace-loader-spinner" />
          </div>
        )
      ) : (
        <>
          <div
            className="workspace-summary-strip diagnostics-summary"
            aria-label="Resumen de procesamiento"
          >
            {[
              ["Total", data.statistics.total],
              ["Procesadas", data.statistics.processed],
              ["Pendientes", data.statistics.pending],
              ["Progreso", `${data.statistics.processed_percentage}%`],
            ].map(([label, value]) => (
              <div key={label}>
                <span>{label}</span>
                <strong>{value}</strong>
              </div>
            ))}
          </div>
          {data.results.length ? (
            <div className="workspace-table-frame">
              <div className="workspace-table-scroll">
                <p className="table-scroll-hint">
                  <i className="bi bi-arrow-left-right" aria-hidden="true" />
                  Desliza la tabla para ver todas las columnas
                </p>
                <table className="workspace-data-table">
                  <caption className="co-sr-only">
                    Imágenes para diagnóstico
                  </caption>
                  <thead>
                    <tr>
                      <th scope="col">Imagen</th>
                      <th scope="col">Paciente</th>
                      <th scope="col">Tipo</th>
                      <th scope="col">Descripción</th>
                      <th scope="col">Estado</th>
                      <th scope="col">Acción</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.results.map((image) => (
                      <tr key={image.id}>
                        <td data-label="Imagen">
                          <ProtectedThumbnail
                            path={`clinics/clinical-images/${image.id}/original/file/`}
                            className="clinical-result-thumbnail"
                            alt={image.descripcion}
                          />
                        </td>
                        <td data-label="Paciente">{image.patient_name}</td>
                        <td data-label="Tipo">{image.tipo_imagen}</td>
                        <td data-label="Descripción">{image.descripcion}</td>
                        <td data-label="Estado">
                          <span
                            className={`appointment-status ${image.resultados_url ? "is-completed" : "is-pending"}`}
                          >
                            {image.resultados_url ? "Procesada" : "Pendiente"}
                          </span>
                        </td>
                        <td
                          data-label="Acciones"
                          className="clinical-result-actions"
                        >
                          <Link
                            className="clinical-action-primary clinical-action-compact"
                            to={`/diagnostics/${image.id}`}
                          >
                            {image.resultados_url
                              ? "Ver / repetir análisis"
                              : "Analizar"}
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="workspace-empty-state">
              <span>No se encontraron imágenes para estos filtros.</span>
              {params.toString() && (
                <button
                  type="button"
                  className="clinical-action-outline co-mt-3"
                  onClick={() => {
                    setFilters({ patient: "", type: "", date: "" });
                    setParams({});
                  }}
                >
                  Limpiar filtros
                </button>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
