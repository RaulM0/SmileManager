import type { ReactNode } from "react";

// Shared clinical workspace primitives: the same surfaces, controls and states as patients.
export function AdminSection({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: ReactNode;
}) {
  return (
    <section className="workspace-section">
      <div className="workspace-section-heading">
        <div>
          <h2>{title}</h2>
          {description && <p>{description}</p>}
        </div>
      </div>
      {children}
    </section>
  );
}

export function AdminState({
  pending,
  error,
  empty,
  children,
}: {
  pending?: boolean;
  error?: boolean;
  empty?: string;
  children?: ReactNode;
}) {
  if (pending)
    return (
      <div className="workspace-empty-state" role="status">
        <span className="workspace-loader-spinner" aria-hidden="true" />
        Cargando información…
      </div>
    );
  if (error)
    return (
      <div className="workspace-inline-error co-m-4" role="alert">
        No fue posible cargar la información. Inténtalo de nuevo.
      </div>
    );
  if (empty)
    return (
      <div className="workspace-empty-state co-p-4">
        <i className="bi bi-inbox" aria-hidden="true" />
        <span>{empty}</span>
      </div>
    );
  return <>{children}</>;
}

const statuses: Record<string, string> = {
  ACTIVE: "Activo",
  INACTIVE: "Inactivo",
  SUSPENDED: "Suspendido",
  REVOKED: "Revocado",
  PENDING: "Pendiente",
  ACCEPTED: "Aceptada",
  REJECTED: "Rechazada",
  EXPIRED: "Vencida",
  RUNNING: "En curso",
  SUCCEEDED: "Completada",
  FAILED: "Fallida",
};
export function AdminStatus({
  value,
  label,
}: {
  value: string;
  label?: string;
}) {
  const tone = ["ACTIVE", "ACCEPTED", "SUCCEEDED"].includes(value)
    ? "is-active"
    : "is-inactive";
  return (
    <span className={`patient-status ${tone}`}>
      {label ?? statuses[value] ?? value}
    </span>
  );
}

export function AdminPagination({
  page,
  count,
  next,
  busy,
  onPage,
  label,
}: {
  page: number;
  count?: number;
  next?: string | null;
  busy?: boolean;
  onPage: (page: number) => void;
  label: string;
}) {
  return (
    <nav className="workspace-pagination co-p-4" aria-label={label}>
      <span className="workspace-pagination-summary">
        Página {page} · {count ?? 0} registros
      </span>
      <div className="co-flex co-gap-2">
        <button
          type="button"
          className="clinical-action-outline clinical-action-compact"
          disabled={busy || page === 1}
          onClick={() => onPage(page - 1)}
        >
          Anterior
        </button>
        <button
          type="button"
          className="clinical-action-outline clinical-action-compact"
          disabled={busy || !next}
          onClick={() => onPage(page + 1)}
        >
          Siguiente
        </button>
      </div>
    </nav>
  );
}
