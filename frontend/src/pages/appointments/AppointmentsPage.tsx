import { useMemo, useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";
import { getErrorMessage } from "../../api/client";
import { formatDate } from "../../utils/date";
import type { Appointment } from "../../types/domain";
import { useToast } from "../../context/ToastContext";
import { appointmentsService } from "../../services/appointments";
import { queryKeys } from "../../query/keys";
import { ConfirmDialog } from "../../components/ConfirmDialog";
import { appointmentStatus } from "../../utils/appointmentStatus";

const weekdays = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"];

function localDateKey(date: Date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function AppointmentCalendar({
  appointments,
  month,
  onMonthChange,
}: {
  appointments: Appointment[];
  month?: Date;
  onMonthChange?: (date: Date) => void;
}) {
  const [mobileView, setMobileView] = useState("agenda");
  const [internalMonth, setVisibleMonth] = useState(() => {
    const now = new Date();
    return new Date(now.getFullYear(), now.getMonth(), 1);
  });
  const visibleMonth = month ?? internalMonth;
  const byDate = useMemo(
    () =>
      appointments.reduce<Record<string, Appointment[]>>(
        (result, appointment) => {
          (result[appointment.fecha] ||= []).push(appointment);
          return result;
        },
        {},
      ),
    [appointments],
  );
  const first = new Date(
    visibleMonth.getFullYear(),
    visibleMonth.getMonth(),
    1,
  );
  const gridStart = new Date(first);
  gridStart.setDate(first.getDate() - first.getDay());
  const days = Array.from({ length: 42 }, (_, index) => {
    const value = new Date(gridStart);
    value.setDate(gridStart.getDate() + index);
    return value;
  });
  const title = new Intl.DateTimeFormat("es-MX", {
    month: "long",
    year: "numeric",
  }).format(first);
  const monthKey = localDateKey(first).slice(0, 7);
  const monthDates = Object.entries(byDate)
    .filter(([date]) => date.startsWith(monthKey))
    .sort(([left], [right]) => left.localeCompare(right));
  function move(months: number) {
    const next = new Date(
      visibleMonth.getFullYear(),
      visibleMonth.getMonth() + months,
      1,
    );
    setVisibleMonth(next);
    onMonthChange?.(next);
  }

  return (
    <section className="clinical-calendar" aria-label="Calendario de citas">
      <div className="clinical-calendar-header">
        <button
          type="button"
          className="clinical-action-outline clinical-calendar-nav"
          onClick={() => move(-1)}
          aria-label="Mes anterior"
        >
          <i className="bi bi-chevron-left" aria-hidden="true" />
        </button>
        <div className="clinical-calendar-heading">
          <h2>{title}</h2>
          <button
            type="button"
            className="clinical-calendar-today"
            onClick={() => {
              const now = new Date();
              setVisibleMonth(new Date(now.getFullYear(), now.getMonth(), 1));
              onMonthChange?.(new Date(now.getFullYear(), now.getMonth(), 1));
            }}
          >
            Hoy
          </button>
        </div>
        <button
          type="button"
          className="clinical-action-outline clinical-calendar-nav"
          onClick={() => move(1)}
          aria-label="Mes siguiente"
        >
          <i className="bi bi-chevron-right" aria-hidden="true" />
        </button>
      </div>
      <div
        className="clinical-calendar-view-switch"
        role="group"
        aria-label="Vista del calendario"
      >
        <button
          type="button"
          className="clinical-action-outline clinical-action-compact"
          aria-pressed={mobileView === "agenda"}
          onClick={() => setMobileView("agenda")}
        >
          Agenda
        </button>
        <button
          type="button"
          className="clinical-action-outline clinical-action-compact"
          aria-pressed={mobileView === "month"}
          onClick={() => setMobileView("month")}
        >
          Mes
        </button>
      </div>
      <div
        className={`clinical-calendar-grid ${mobileView === "agenda" ? "is-mobile-hidden" : ""}`}
      >
        <p className="calendar-scroll-hint">
          <i className="bi bi-arrow-left-right" aria-hidden="true" />
          Desliza el calendario para ver toda la semana
        </p>
        <div className="clinical-calendar-grid-inner">
          <div className="clinical-calendar-weekdays" aria-hidden="true">
            {weekdays.map((day) => (
              <div key={day}>{day}</div>
            ))}
          </div>
          <div className="clinical-calendar-days">
            {days.map((date) => {
              const key = localDateKey(date);
              const outside = date.getMonth() !== visibleMonth.getMonth();
              const today = key === localDateKey(new Date());
              return (
                <div
                  className={`clinical-calendar-day ${outside ? "is-outside" : ""}`}
                  key={key}
                >
                  <div
                    className={`clinical-calendar-date ${today ? "is-today" : ""}`}
                  >
                    {date.getDate()}
                  </div>
                  {(byDate[key] || []).map((item) => (
                    <Link
                      className={`clinical-calendar-entry ${appointmentStatus[item.estatus]?.className || ""}`}
                      aria-label={`${item.hora.slice(0, 5)} ${item.paciente.full_name}, ${appointmentStatus[item.estatus]?.label || item.estatus}`}
                      title={`${item.hora.slice(0, 5)} ${item.paciente.full_name} · ${appointmentStatus[item.estatus]?.label || item.estatus}`}
                      to={`/appointments/${item.id}`}
                      key={item.id}
                    >
                      <span className="clinical-calendar-entry-meta">
                        <time dateTime={item.hora}>
                          {item.hora.slice(0, 5)}
                        </time>
                        <span>
                          {appointmentStatus[item.estatus]?.label ||
                            item.estatus}
                        </span>
                      </span>
                      <span className="clinical-calendar-entry-patient">
                        {item.paciente.full_name}
                      </span>
                    </Link>
                  ))}
                </div>
              );
            })}
          </div>
        </div>
      </div>
      <div
        className={`clinical-calendar-agenda ${mobileView === "agenda" ? "is-active" : ""}`}
      >
        {monthDates.length ? (
          monthDates.map(([date, entries]) => (
            <section
              className="clinical-calendar-date-group"
              key={date}
              aria-label={new Intl.DateTimeFormat("es-MX", {
                dateStyle: "full",
              }).format(new Date(`${date}T12:00:00`))}
            >
              <h3>
                <time dateTime={date}>
                  {new Intl.DateTimeFormat("es-MX", {
                    weekday: "long",
                    day: "numeric",
                    month: "short",
                  }).format(new Date(`${date}T12:00:00`))}
                </time>
              </h3>
              {entries
                .slice()
                .sort((left, right) => left.hora.localeCompare(right.hora))
                .map((item) => (
                  <Link
                    className="clinical-calendar-agenda-row"
                    to={`/appointments/${item.id}`}
                    key={item.id}
                  >
                    <time className="time-value" dateTime={item.hora}>
                      {item.hora.slice(0, 5)}
                    </time>
                    <span className="clinical-calendar-agenda-patient">
                      {item.paciente.full_name}
                      <small>{item.motivo}</small>
                    </span>
                    <span
                      className={`appointment-status ${appointmentStatus[item.estatus]?.className || ""}`}
                    >
                      {appointmentStatus[item.estatus]?.label || item.estatus}
                    </span>
                  </Link>
                ))}
            </section>
          ))
        ) : (
          <p className="clinical-calendar-empty">
            No hay citas para este mes con los filtros actuales.
          </p>
        )}
      </div>
    </section>
  );
}

export default function AppointmentsPage() {
  const toast = useToast();
  const queryClient = useQueryClient();
  const [params, setParams] = useSearchParams();
  const status = params.get("status") || "";
  const search = params.get("search") || "";
  const [term, setTerm] = useState(search);
  const [cancelTarget, setCancelTarget] = useState<Appointment | null>(null);
  const [page, setPage] = useState(1);
  const [month, setMonth] = useState(() => {
    const now = new Date();
    return new Date(now.getFullYear(), now.getMonth(), 1);
  });
  const start = new Date(month);
  start.setDate(start.getDate() - start.getDay());
  const end = new Date(start);
  end.setDate(end.getDate() + 41);
  const from = localDateKey(start),
    to = localDateKey(end);
  const listing = useQuery({
    queryKey: [...queryKeys.appointmentList(status, search), page],
    queryFn: () => appointmentsService.list(status, search, page),
  });
  const calendar = useQuery({
    queryKey: [...queryKeys.appointments, "calendar", status, search, from, to],
    queryFn: () => appointmentsService.range(status, search, from, to),
  });
  const items: Appointment[] | undefined = listing.data?.results;
  const error = listing.error?.message ?? "";
  const actionMutation = useMutation({
    mutationFn: ({ id, name }: { id: number; name: "complete" | "cancel" }) =>
      appointmentsService.transition(id, name),
    onSuccess: async (updated, { name }) => {
      queryClient.setQueryData(
        queryKeys.resource(`clinics/appointments/${updated.id}/`),
        updated,
      );
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.appointments }),
        queryClient.invalidateQueries({
          queryKey: queryKeys.resource("clinics/dashboard/"),
        }),
      ]);
      toast.success(
        name === "complete" ? "Cita completada." : "Cita cancelada.",
      );
    },
    onError: (requestError) => toast.error(getErrorMessage(requestError)),
  });
  const busyId = actionMutation.isPending ? actionMutation.variables?.id : null;
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPage(1);
    setParams({ ...Object.fromEntries(params), search: term });
  }
  function selectStatus(value: string) {
    setPage(1);
    setParams({
      ...(search ? { search } : {}),
      ...(value ? { status: value } : {}),
    });
  }
  return (
    <div className="workspace-page co-mx-auto co-max-w-[1560px]">
      <div className="workspace-page-header">
        <div>
          <h1>Agenda</h1>
        </div>
        <Link to="/appointments/new" className="clinical-action-primary">
          <i className="bi bi-plus-circle" aria-hidden="true" />
          Nueva cita
        </Link>
      </div>
      <div
        className="workspace-filter-group"
        role="group"
        aria-label="Filtrar citas por estado"
      >
        {[
          ["", "Todas"],
          ["P", "Pendientes"],
          ["C", "Completadas"],
          ["A", "Canceladas"],
        ].map(([value, label]) => (
          <button
            type="button"
            className="workspace-status-filter"
            key={value}
            aria-pressed={status === value}
            onClick={() => selectStatus(value)}
          >
            {label}
          </button>
        ))}
      </div>
      <form onSubmit={submit} className="clinical-search-form" role="search">
        <input
          aria-label="Buscar citas"
          className="clinical-form-control"
          type="search"
          value={term}
          onChange={(event) => setTerm(event.target.value)}
          placeholder="Paciente, teléfono o ID"
        />
        <button className="clinical-action-outline">Buscar</button>
      </form>
      {error && (
        <div
          className={
            items
              ? "workspace-inline-warning co-mb-4"
              : "workspace-inline-error co-mb-4"
          }
          role="alert"
        >
          {error}
          {items && <span> Se muestran las citas de la última carga.</span>}
          <button
            className="clinical-action-outline co-ml-3"
            onClick={() => void listing.refetch()}
          >
            Reintentar
          </button>
        </div>
      )}
      {listing.isFetching && items && (
        <p className="clinical-loading-note" role="status">
          Actualizando citas…
        </p>
      )}
      {!items && !error ? (
        <div className="page-loader" role="status" aria-label="Cargando citas">
          <div className="workspace-loader-spinner" />
        </div>
      ) : items ? (
        <>
          {calendar.data ? (
            <AppointmentCalendar
              appointments={calendar.data}
              month={month}
              onMonthChange={setMonth}
            />
          ) : calendar.error ? (
            <div role="alert">
              No se pudo cargar el calendario.{" "}
              <button onClick={() => void calendar.refetch()}>
                Reintentar
              </button>
            </div>
          ) : (
            <p role="status">Cargando calendario…</p>
          )}
          <h2 className="workspace-section-heading">
            Todas las citas que coinciden con los filtros
          </h2>
          <div className="workspace-table-frame">
            <div className="workspace-table-scroll">
              <p className="table-scroll-hint">
                <i className="bi bi-arrow-left-right" aria-hidden="true" />
                Desliza la tabla para ver todas las columnas
              </p>
              <table
                className="workspace-data-table"
                aria-busy={listing.isFetching}
              >
                <caption className="co-sr-only">
                  Citas según el filtro seleccionado
                </caption>
                <thead>
                  <tr>
                    <th scope="col">Fecha</th>
                    <th scope="col">Hora</th>
                    <th scope="col">Paciente</th>
                    <th scope="col">Motivo</th>
                    <th scope="col">Estado</th>
                    <th scope="col">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr key={item.id}>
                      <td data-label="Fecha">
                        <time dateTime={item.fecha}>
                          {formatDate(item.fecha)}
                        </time>
                      </td>
                      <td data-label="Hora">{item.hora.slice(0, 5)}</td>
                      <td data-label="Paciente">{item.paciente.full_name}</td>
                      <td data-label="Motivo">{item.motivo}</td>
                      <td data-label="Estado">
                        <span
                          className={`appointment-status ${appointmentStatus[item.estatus]?.className || ""}`}
                        >
                          {appointmentStatus[item.estatus]?.label ||
                            item.estatus}
                        </span>
                      </td>
                      <td data-label="Acciones">
                        <Link
                          className="clinical-action-outline clinical-action-compact co-mr-1"
                          to={`/appointments/${item.id}`}
                        >
                          Ver
                        </Link>
                        <Link
                          className="clinical-action-outline clinical-action-compact co-mr-1"
                          to={`/appointments/${item.id}/edit`}
                        >
                          Editar
                        </Link>
                        {item.estatus === "P" && (
                          <>
                            <button
                              type="button"
                              className="clinical-action-success co-mr-1"
                              disabled={busyId === item.id}
                              onClick={() =>
                                actionMutation.mutate({
                                  id: item.id,
                                  name: "complete",
                                })
                              }
                            >
                              Completar
                            </button>
                            <button
                              type="button"
                              className="clinical-action-danger"
                              disabled={busyId === item.id}
                              onClick={() => setCancelTarget(item)}
                            >
                              Cancelar
                            </button>
                          </>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {!items.length && (
              <div className="workspace-empty-state">
                <span>No se encontraron citas.</span>
                {(search || status) && (
                  <button
                    type="button"
                    className="clinical-action-outline co-mt-3"
                    onClick={() => {
                      setTerm("");
                      setParams({});
                    }}
                  >
                    Limpiar filtros
                  </button>
                )}
              </div>
            )}
          </div>
          <nav className="workspace-pagination" aria-label="Páginas de citas">
            <button
              className="clinical-action-outline clinical-action-compact"
              type="button"
              disabled={page === 1 || listing.isFetching}
              onClick={() => setPage(page - 1)}
            >
              Anterior
            </button>
            <span className="workspace-pagination-summary" aria-live="polite">
              Página {page}
            </span>
            <button
              className="clinical-action-outline clinical-action-compact"
              type="button"
              disabled={!listing.data?.next || listing.isFetching}
              onClick={() => setPage(page + 1)}
            >
              Siguiente
            </button>
          </nav>
        </>
      ) : (
        <button
          className="clinical-action-outline"
          onClick={() => void listing.refetch()}
        >
          Reintentar
        </button>
      )}
      {cancelTarget && (
        <ConfirmDialog
          title="Cancelar cita"
          confirmLabel="Sí, cancelar cita"
          busyLabel="Cancelando…"
          busy={actionMutation.isPending}
          onClose={() => setCancelTarget(null)}
          onConfirm={() =>
            actionMutation.mutate(
              { id: cancelTarget.id, name: "cancel" },
              { onSuccess: () => setCancelTarget(null) },
            )
          }
        >
          <p>
            Se cancelará la cita de{" "}
            <strong>{cancelTarget.paciente.full_name}</strong> del{" "}
            {formatDate(cancelTarget.fecha)} a las{" "}
            {cancelTarget.hora.slice(0, 5)}. La cita quedará marcada como
            cancelada en la agenda.
          </p>
        </ConfirmDialog>
      )}
    </div>
  );
}
