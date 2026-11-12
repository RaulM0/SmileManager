import { useState } from "react";
import { useParams } from "react-router-dom";
import { getErrorMessage } from "../../api/client";
import type { ClinicalImage } from "../../types/domain";
import { useToast } from "../../context/ToastContext";
import { ProtectedThumbnail } from "../../components/images/ProtectedImage";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { imagesService } from "../../services/images";
import { queryKeys } from "../../query/keys";
import { clinicalService } from "../../services/clinical";
import { useApiDownload } from "../../hooks/useApiDownload";

export default function ClinicalImageListPage({ searchable = false }: { searchable?: boolean }) {
  const toast = useToast();
  const queryClient = useQueryClient();
  const { id } = useParams();
  const [filters, setFilters] = useState({ date: "", consultation_id: "" });
  const [page, setPage] = useState(1);
  const [consultationPage, setConsultationPage] = useState(1);
  const { active: downloadActive, download } = useApiDownload();
  const listing = useQuery({ queryKey: [...queryKeys.images(id!), filters.date, filters.consultation_id, page], queryFn: () => imagesService.list(id!, filters.date, filters.consultation_id, page) });
  const consultationQuery = useQuery({ queryKey: [...queryKeys.resource(`clinics/patients/${id}/consultations/`), consultationPage], queryFn: () => clinicalService.consultations(id!, consultationPage) });
  const items: ClinicalImage[] | undefined = listing.data?.results;
  const error = listing.error?.message ?? "";
  const consultations = consultationQuery.data?.results ?? [];
  const consultationError = consultationQuery.error?.message ?? "";
  const consultationsLoading = consultationQuery.isPending;
  const deletion = useMutation({
    mutationFn: imagesService.remove,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.images(id!) }),
        queryClient.invalidateQueries({ queryKey: queryKeys.diagnostics }),
      ]);
      toast.success("Imagen clínica eliminada.");
    },
    onError: (requestError) => toast.error(`No se pudo eliminar la imagen. ${getErrorMessage(requestError)}`),
  });
  function remove(imageId: number) {
    if (!window.confirm("¿Deseas eliminar esta imagen clínica?")) return;
    deletion.mutate(imageId);
  }
  const deletingId = deletion.isPending ? deletion.variables : null;
  return (
    <div className="workspace-page co-mx-auto co-max-w-[1320px]">
      <div className="workspace-page-header"><div><h1>
        {searchable ? "Buscar imágenes" : "Historial de imágenes"}
      </h1></div></div>
      {error && <div className={items ? "workspace-inline-warning co-mb-4" : "workspace-inline-error co-mb-4"} role="alert">{error}{items && <span> Se muestran las imágenes de la última carga.</span>}<button className="clinical-action-outline co-ml-3" onClick={() => void listing.refetch()}>Reintentar listado</button></div>}
      {listing.isFetching && items && <p className="clinical-loading-note" role="status">Actualizando imágenes…</p>}
      {searchable && consultationError && <div className="workspace-inline-warning co-mb-4" role="alert">No se pudieron cargar las consultas. El listado de imágenes sigue disponible. <button className="clinical-action-outline co-ml-3" onClick={() => void consultationQuery.refetch()}>Reintentar consultas</button></div>}
      {searchable && consultationsLoading && <div className="clinical-loading-note" role="status">Cargando consultas…</div>}
      {searchable && (
        <section className="clinical-filter-surface" aria-label="Filtros de imágenes">
            <div className="clinical-filter-grid">
              <div className="clinical-filter-col-5">
                <label htmlFor="filter-date" className="clinical-form-label">
                  Fecha
                </label>
                <input
                  id="filter-date"
                  type="date"
                  className="clinical-form-control"
                  value={filters.date}
                  onChange={(e) =>
                    { setPage(1); setFilters({ ...filters, date: e.target.value }); }
                  }
                />
              </div>
              <div className="clinical-filter-col-7">
                <label htmlFor="filter-consultation" className="clinical-form-label">
                  Consulta
                </label>
                <select
                  id="filter-consultation"
                  className="clinical-form-control"
                  value={filters.consultation_id}
                  onChange={(e) =>
                    { setPage(1); setFilters({ ...filters, consultation_id: e.target.value }); }
                  }
                >
                  <option value="">Todas</option>
                  {filters.consultation_id && !consultations.some((c) => String(c.id) === filters.consultation_id) && <option value={filters.consultation_id}>Consulta seleccionada #{filters.consultation_id}</option>}
                  {consultations.map((c) => (
                    <option key={c.id} value={c.id}>
                      {new Date(c.fecha_consulta).toLocaleString("es-MX")} —{" "}
                      {c.motivo_consulta}
                    </option>
                  ))}
                </select>
                <div className="workspace-pagination"><button className="clinical-action-outline clinical-action-compact" type="button" disabled={consultationPage === 1} onClick={() => setConsultationPage(consultationPage - 1)}>Consultas anteriores</button><span className="workspace-pagination-summary" aria-live="polite">Página {consultationPage}</span><button className="clinical-action-outline clinical-action-compact" type="button" disabled={!consultationQuery.data?.next} onClick={() => setConsultationPage(consultationPage + 1)}>Más consultas</button></div>
              </div>
            </div>
        </section>
      )}
      {!items ? (error ? null : (
        <div className="page-loader" role="status" aria-label="Cargando imágenes">
          <div className="workspace-loader-spinner" />
        </div>
      )) : (
        <>
          {items.length ? (
            <ul className="clinical-image-list" aria-label="Imágenes clínicas guardadas">
              {items.map((image) => (
                <li className="clinical-image-row" key={image.id}>
                  <ProtectedThumbnail
                    path={`clinics/clinical-images/${image.id}/original/file/`}
                    className="clinical-image-thumbnail"
                    alt={image.descripcion}
                  />
                  <div className="clinical-image-details">
                    <h2>{image.tipo_imagen}</h2>
                    <p>{image.descripcion}</p>
                    <time dateTime={image.fecha_subida}>{new Date(image.fecha_subida).toLocaleString("es-MX")}</time>
                  </div>
                  <div className="clinical-image-actions">
                    <a className="clinical-action-primary clinical-action-compact" href={image.imagen_url} download aria-disabled={downloadActive !== null} onClick={(event) => {
                      event.preventDefault();
                      void download(String(image.id), `clinics/clinical-images/${image.id}/original/file/`, `Imagen_${image.id}`);
                    }}>
                      {downloadActive === String(image.id) ? "Preparando…" : "Descargar"}
                    </a>
                    <button
                      className="clinical-action-danger"
                      disabled={deletingId === image.id}
                      onClick={() => remove(image.id)}
                    >
                      {deletingId === image.id ? "Eliminando…" : "Eliminar"}
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="workspace-empty-state"><span>{filters.date || filters.consultation_id ? "No hay imágenes clínicas para los filtros actuales." : "No hay imágenes clínicas."}</span>{searchable && (filters.date || filters.consultation_id) && <button type="button" className="clinical-action-outline co-mt-3" onClick={() => { setPage(1); setFilters({ date: "", consultation_id: "" }); }}>Limpiar filtros</button>}</div>
          )}
          <nav className="workspace-pagination" aria-label="Páginas de imágenes"><button className="clinical-action-outline clinical-action-compact" disabled={page === 1 || listing.isFetching} onClick={() => setPage(page - 1)}>Anterior</button><span className="workspace-pagination-summary" aria-live="polite">Página {page}</span><button className="clinical-action-outline clinical-action-compact" disabled={!listing.data?.next || listing.isFetching} onClick={() => setPage(page + 1)}>Siguiente</button></nav>
        </>
      )}
    </div>
  );
}
