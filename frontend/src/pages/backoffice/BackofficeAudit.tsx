import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { AdminState } from "../../components/workspace/Administration";
import type { Paginated } from "../../types/domain";
import { Load, Pages, Events } from "./shared";
import { useAdmin } from "./useAdmin";
import type { Event } from "./types";

export function BackofficeAudit() {
  const [paramsFromUrl] = useSearchParams();
  const [page, setPage] = useState(1);
  const [draft, setDraft] = useState({
    action: "",
    resource_type: "",
    outcome: "",
    actor: paramsFromUrl.get("actor") || "",
    from: "",
    to: "",
    request_id: "",
  });
  const [filters, setFilters] = useState(draft);
  const params = new URLSearchParams({ page: String(page), ...filters });
  const query = useAdmin<Paginated<Event>>(`audit/?${params}`);
  return (
    <>
      <div className="workspace-page-header">
        <div>
          <h1>Auditoría</h1>
          <p className="clinical-page-description">
            Consulta los cambios administrativos y filtra por fecha, usuario o
            resultado.
          </p>
        </div>
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          setPage(1);
          setFilters(draft);
        }}
        className="clinical-filter-surface admin-form-grid"
      >
        {Object.entries({
          action: "Acción",
          resource_type: "Tipo de recurso",
          outcome: "Resultado",
          actor: "ID de actor",
          from: "Desde",
          to: "Hasta",
          request_id: "ID de solicitud",
        }).map(([key, label]) => (
          <label className="clinical-form-label" key={key}>
            {label}
            <input
              type={key === "from" || key === "to" ? "date" : "text"}
              className="clinical-form-control"
              value={draft[key as keyof typeof draft]}
              onChange={(e) => setDraft({ ...draft, [key]: e.target.value })}
            />
          </label>
        ))}
        <button className="clinical-action-primary co-self-end">
          Aplicar filtros
        </button>
      </form>
      <Load pending={query.isPending} error={query.error}>
        {query.data && (
          <>
            {query.data.results.length ? (
              <Events events={query.data.results} />
            ) : (
              <AdminState empty="No hay eventos con este filtro." />
            )}
            <Pages page={page} setPage={setPage} data={query.data} />
          </>
        )}
      </Load>
    </>
  );
}
