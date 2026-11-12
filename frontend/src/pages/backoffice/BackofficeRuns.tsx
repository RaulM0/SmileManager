import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  AdminState,
  AdminStatus,
} from "../../components/workspace/Administration";
import type { Paginated } from "../../types/domain";
import { Load, Pages } from "./shared";
import { useAdmin } from "./useAdmin";
import { date } from "./date";
import type { Run } from "./types";

export function BackofficeRuns() {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("");
  const [model, setModel] = useState("");
  const [failure, setFailure] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const params = new URLSearchParams({
    page: String(page),
    status,
    model_version: model,
    failure_category: failure,
    from,
    to,
  });
  const query = useAdmin<Paginated<Run>>(`ai-runs/?${params}`);
  return (
    <>
      <div className="workspace-page-header">
        <div>
          <h1>Ejecuciones de IA</h1>
          <p className="clinical-page-description">
            Supervisa el estado y el historial de los análisis.
          </p>
        </div>
      </div>
      <div className="clinical-filter-surface admin-form-grid">
        <label className="clinical-form-label">
          Estado
          <select
            className="clinical-form-control"
            value={status}
            onChange={(e) => {
              setPage(1);
              setStatus(e.target.value);
            }}
          >
            <option value="">Todos</option>
            <option>RUNNING</option>
            <option>SUCCEEDED</option>
            <option>FAILED</option>
          </select>
        </label>
        {[
          [model, setModel, "Versión del modelo", "text"],
          [failure, setFailure, "Categoría de fallo", "text"],
          [from, setFrom, "Desde", "date"],
          [to, setTo, "Hasta", "date"],
        ].map(([value, setter, label, type]) => (
          <label className="clinical-form-label" key={label as string}>
            {label as string}
            <input
              type={type as string}
              className="clinical-form-control"
              value={value as string}
              onChange={(e) => {
                setPage(1);
                (setter as (s: string) => void)(e.target.value);
              }}
            />
          </label>
        ))}
      </div>
      <Load pending={query.isPending} error={query.error}>
        {query.data && (
          <>
            {query.data.results.length ? (
              <ul className="co-bg-white co-border co-border-[#dce3e6] co-rounded co-divide-y">
                {query.data.results.map((r) => (
                  <li
                    key={r.id}
                    className="co-p-4 co-flex co-justify-between co-gap-3 co-flex-wrap"
                  >
                    <div>
                      <Link
                        className="co-font-semibold"
                        to={`/backoffice/ai/${r.id}`}
                      >
                        Ejecución #{r.id}
                      </Link>
                      <p className="co-text-sm">
                        {date(r.requested_at)} · {r.model_name}
                      </p>
                    </div>
                    <AdminStatus
                      value={r.status}
                      label={
                        r.potentially_stale
                          ? "Posiblemente detenida"
                          : undefined
                      }
                    />
                  </li>
                ))}
              </ul>
            ) : (
              <AdminState empty="No hay ejecuciones de IA con este filtro." />
            )}
            <Pages page={page} setPage={setPage} data={query.data} />
          </>
        )}
      </Load>
    </>
  );
}

export function BackofficeRun() {
  const { id } = useParams();
  const q = useAdmin<Run>(`ai-runs/${id}/`);
  const r = q.data;
  return (
    <>
      <Link to="/backoffice/ai">Volver a IA</Link>
      <Load pending={q.isPending} error={q.error}>
        {r && (
          <>
            <h1 className="co-text-2xl co-font-semibold co-my-5">
              Ejecución #{r.id}
            </h1>
            {r.potentially_stale && (
              <p className="workspace-inline-warning co-mb-4">
                La ejecución podría estar detenida. La recuperación requiere el
                procedimiento operacional con workers detenidos.
              </p>
            )}
            <dl className="clinical-form-surface admin-detail-grid">
              {[
                ["Estado", r.status],
                ["Solicitado", date(r.requested_at)],
                ["Iniciado", date(r.started_at)],
                ["Finalizado", date(r.completed_at)],
                ["Solicitante", r.requested_by_id ?? "—"],
                ["Modelo", r.model_name],
                ["Versión", r.model_version],
                ["Fallo", r.failure_category || "—"],
                ["Solicitud", r.request_id],
              ].map(([key, value]) => (
                <div key={key}>
                  <dt>{key}</dt>
                  <dd className="co-break-all">{value}</dd>
                </div>
              ))}
            </dl>
          </>
        )}
      </Load>
    </>
  );
}
