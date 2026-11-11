import type { ReactNode } from "react";
import { AdminState } from "../../components/workspace/Administration";
import type { Paginated } from "../../types/domain";
import { auditActionLabel } from "../../utils/auditLabels";
import type { Event } from "./types";
import { date } from "./date";

export function Load({
  pending,
  error,
  children,
}: {
  pending: boolean;
  error: Error | null;
  children: ReactNode;
}) {
  if (pending) return <AdminState pending />;
  if (error) return <AdminState error />;
  return <>{children}</>;
}

export function Pages({
  page,
  setPage,
  data,
}: {
  page: number;
  setPage: (page: number) => void;
  data?: Paginated<unknown>;
}) {
  return (
    <nav aria-label="Paginación" className="workspace-pagination">
      <button
        className="clinical-action-outline clinical-action-compact"
        disabled={page === 1}
        onClick={() => setPage(page - 1)}
      >
        Anterior
      </button>
      <span className="workspace-pagination-summary">
        Página {page} · {data?.count ?? 0} registros
      </span>
      <button
        className="clinical-action-outline clinical-action-compact"
        disabled={!data?.next}
        onClick={() => setPage(page + 1)}
      >
        Siguiente
      </button>
    </nav>
  );
}

export function Events({ events }: { events: Event[] }) {
  return (
    <ul className="admin-activity-list clinical-form-surface">
      {events.map((e) => (
        <li key={e.id} className="co-p-4 co-text-sm">
          <div className="co-flex co-flex-wrap co-justify-between co-gap-2">
            <strong>{auditActionLabel(e.action)}</strong>
            <time>{date(e.timestamp)}</time>
          </div>
          <p className="co-mt-1">
            {e.actor_username || "Sistema"} · {e.resource_type} #{e.resource_id}{" "}
            · {e.outcome}
          </p>
          <p className="co-text-[#52616a] co-break-all">
            Solicitud: {e.request_id}
          </p>
        </li>
      ))}
    </ul>
  );
}
