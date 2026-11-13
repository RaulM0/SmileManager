import { useToast } from "../../context/ToastContext";
import { useState } from "react";
import type { FormEvent } from "react";
import {
  Link,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../api/client";
import type { Paginated } from "../../types/domain";
import { ConfirmDialog } from "../../components/ConfirmDialog";

type Patient = {
  id: number;
  nombre: string;
  appat: string;
  apmat: string;
  estatus: string;
  medico: string | null;
  medico_id: number | null;
  appointments_count?: number;
  consultations_count?: number;
  images_count?: number;
  updated: string;
  fecha_nacimiento: string;
  genero: string;
  telefono: string;
  email: string;
};
type Appointment = {
  id: number;
  patient_id: number;
  patient: string;
  doctor: string | null;
  fecha: string;
  hora: string;
  estatus: string;
};
type RecordRow = Record<string, unknown> & { id: number };
const sections = [
  ["history", "Antecedentes"],
  ["consultations", "Consultas"],
  ["odontogram", "Odontograma"],
  ["images", "Imágenes"],
  ["ai", "IA"],
  ["studies", "Estudios"],
  ["consents", "Consentimientos"],
  ["revisions", "Revisiones"],
  ["audit", "Auditoría"],
] as const;

function useData<T>(path: string) {
  return useQuery<T>({
    queryKey: ["backoffice", path],
    queryFn: () => api<T>(`backoffice/${path}`),
    retry: false,
  });
}
function Pager({
  page,
  setPage,
  data,
}: {
  page: number;
  setPage: (n: number) => void;
  data?: Paginated<unknown>;
}) {
  return (
    <nav className="workspace-pagination" aria-label="Paginación">
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
function State({ pending, error }: { pending: boolean; error: Error | null }) {
  return pending ? (
    <p role="status">Cargando información…</p>
  ) : error ? (
    <p className="workspace-inline-error" role="alert">
      No fue posible cargar la información.
    </p>
  ) : null;
}
function ReadOnlyValue({ value }: { value: unknown }) {
  if (value === null || value === undefined || value === "") return <>—</>;
  if (typeof value === "boolean") return <>{value ? "Sí" : "No"}</>;
  if (Array.isArray(value))
    return value.length ? (
      <ul className="co-pl-4">
        {value.map((entry, index) => (
          <li key={index}>
            <ReadOnlyValue value={entry} />
          </li>
        ))}
      </ul>
    ) : (
      <>Sin datos</>
    );
  if (typeof value === "object") {
    const entries = Object.entries(value);
    return entries.length ? (
      <dl className="co-pl-3 co-border-l co-border-solid co-border-[#dce3e6]">
        {entries.map(([key, entry]) => (
          <div key={key} className="co-mt-2">
            <dt className="co-font-medium">{key.replaceAll("_", " ")}</dt>
            <dd>
              <ReadOnlyValue value={entry} />
            </dd>
          </div>
        ))}
      </dl>
    ) : (
      <>Sin datos</>
    );
  }
  return <>{String(value)}</>;
}

export function BackofficePatients() {
  const [params] = useSearchParams();
  const doctor = params.get("doctor") || "";
  const [draft, setDraft] = useState("");
  const [search, setSearch] = useState("");
  const [state, setState] = useState("");
  const [page, setPage] = useState(1);
  const q = useData<Paginated<Patient>>(
    `patients/?${new URLSearchParams({ doctor, search, state, page: String(page) })}`,
  );
  return (
    <>
      <div className="workspace-page-header">
        <div>
          <h1>Pacientes</h1>
          <p className="clinical-page-description">
            Consulta administrativa global de pacientes
          </p>
        </div>
      </div>
      {doctor && (
        <p className="clinical-page-description co-mb-4">
          Mostrando pacientes del usuario #{doctor}.{" "}
          <Link to="/backoffice/patients">Ver todos</Link>
        </p>
      )}
      <form
        className="clinical-search-form"
        onSubmit={(e) => {
          e.preventDefault();
          setPage(1);
          setSearch(draft);
        }}
      >
        <input
          className="clinical-form-control"
          aria-label="Buscar pacientes"
          placeholder="Nombre o apellidos"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
        />
        <select
          className="clinical-form-control"
          aria-label="Estado"
          value={state}
          onChange={(e) => {
            setState(e.target.value);
            setPage(1);
          }}
        >
          <option value="">Todos</option>
          <option value="A">Activos</option>
          <option value="I">Inactivos</option>
        </select>
        <button className="clinical-action-primary">Buscar</button>
      </form>
      <State pending={q.isPending} error={q.error} />
      {q.data && (
        <>
          {q.data.results.length ? (
            <div className="workspace-table-frame">
              <div className="workspace-table-scroll">
                <table className="workspace-data-table">
                  <caption className="co-sr-only">Pacientes</caption>
                  <thead>
                    <tr>
                      <th>Paciente</th>
                      <th>Médico responsable</th>
                      <th>Estado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {q.data.results.map((p) => (
                      <tr key={p.id}>
                        <td data-label="Paciente">
                          <Link to={`/backoffice/patients/${p.id}`}>
                            {p.nombre} {p.appat} {p.apmat}
                          </Link>
                        </td>
                        <td data-label="Médico">{p.medico || "Sin asignar"}</td>
                        <td data-label="Estado">
                          <span
                            className={`patient-status ${p.estatus === "A" ? "is-active" : "is-inactive"}`}
                          >
                            {p.estatus === "A" ? "Activo" : "Inactivo"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="workspace-empty-state">
              No hay pacientes con este filtro.
            </div>
          )}
          <Pager page={page} setPage={setPage} data={q.data} />
        </>
      )}
    </>
  );
}

export function BackofficePatient() {
  const { id } = useParams();
  const q = useData<Patient>(`patients/${id}/`);
  const p = q.data;
  return (
    <>
      <Link to="/backoffice/patients">Volver a pacientes</Link>
      <State pending={q.isPending} error={q.error} />
      {p && (
        <>
          <div className="workspace-page-header co-mt-4">
            <div>
              <h1>
                {p.nombre} {p.appat} {p.apmat}
              </h1>
              <p className="clinical-page-description">
                Expediente administrativo · Solo lectura
              </p>
            </div>
            <Link
              className="clinical-action-outline"
              to={`/backoffice/patients/${p.id}/edit`}
            >
              Editar datos
            </Link>
          </div>
          <div className="workspace-summary-strip backoffice-summary-strip">
            <div>
              <span>Médico responsable</span>
              <strong>{p.medico || "Sin asignar"}</strong>
            </div>
            <div>
              <span>Citas</span>
              <strong>{p.appointments_count}</strong>
            </div>
            <div>
              <span>Consultas</span>
              <strong>{p.consultations_count}</strong>
            </div>
            <div>
              <span>Imágenes</span>
              <strong>{p.images_count}</strong>
            </div>
          </div>
          <section className="workspace-section">
            <div className="workspace-section-heading">
              <div>
                <h2>Expediente</h2>
                <p>La consulta de información clínica queda registrada.</p>
              </div>
            </div>
            <nav
              aria-label="Secciones del expediente"
              className="co-grid co-grid-cols-1 sm:co-grid-cols-2 co-gap-3 co-p-4"
            >
              <Link to={`/backoffice/appointments?patient=${p.id}`}>Citas</Link>
              {sections.map(([key, label]) => (
                <Link key={key} to={`/backoffice/patients/${p.id}/${key}`}>
                  {label}
                </Link>
              ))}
            </nav>
          </section>
        </>
      )}
    </>
  );
}

export function BackofficePatientEdit() {
  const toast = useToast();
  const { id } = useParams();
  const navigate = useNavigate();
  const client = useQueryClient();
  const q = useData<Patient>(`patients/${id}/`);
  const [draft, setForm] = useState<Patient | null>(null);
  const form = draft ?? q.data ?? null;
  const [confirm, setConfirm] = useState(false);
  const save = useMutation({
    mutationFn: (value: Patient) =>
      api(`backoffice/patients/${id}/`, {
        method: "PATCH",
        body: JSON.stringify({
          nombre: value.nombre,
          appat: value.appat,
          apmat: value.apmat,
          fecha_nacimiento: value.fecha_nacimiento,
          genero: value.genero,
          telefono: value.telefono,
          email: value.email,
          estatus: value.estatus,
          expected_updated: value.updated,
        }),
      }),
    onSuccess: async () => {
      toast.success("Datos del paciente actualizados.");
      setConfirm(false);
      await client.invalidateQueries({ queryKey: ["backoffice"] });
      navigate(`/backoffice/patients/${id}`);
    },
    onError: () => {
      setConfirm(false);
      toast.error(
        "No se pudieron guardar los cambios. Si otra sesión actualizó el paciente, recarga la información antes de volver a intentarlo.",
      );
    },
  });
  function submit(event: FormEvent) {
    event.preventDefault();
    setConfirm(true);
  }
  return (
    <>
      <Link to={`/backoffice/patients/${id}`}>Volver al paciente</Link>
      <div className="workspace-page-header co-mt-4">
        <div>
          <h1>Editar datos del paciente</h1>
          <p className="clinical-page-description">
            Los cambios se registran en auditoría.
          </p>
        </div>
      </div>
      <State pending={q.isPending} error={q.error} />
      {form && (
        <>
          <form
            onSubmit={submit}
            className="workspace-section co-p-5 co-grid co-gap-4 co-max-w-[680px]"
          >
            {(
              [
                ["nombre", "Nombre", "text"],
                ["appat", "Apellido paterno", "text"],
                ["apmat", "Apellido materno", "text"],
                ["fecha_nacimiento", "Fecha de nacimiento", "date"],
                ["telefono", "Teléfono", "tel"],
                ["email", "Correo", "email"],
              ] as const
            ).map(([key, label, type]) => (
              <label key={key}>
                {label}
                <input
                  className="clinical-form-control"
                  type={type}
                  required
                  value={form[key]}
                  onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                />
              </label>
            ))}
            <label>
              Género
              <select
                className="clinical-form-control"
                value={form.genero}
                onChange={(e) => setForm({ ...form, genero: e.target.value })}
              >
                <option value="F">Femenino</option>
                <option value="M">Masculino</option>
              </select>
            </label>
            <label>
              Estado
              <select
                className="clinical-form-control"
                value={form.estatus}
                onChange={(e) => setForm({ ...form, estatus: e.target.value })}
              >
                <option value="A">Activo</option>
                <option value="I">Inactivo</option>
              </select>
            </label>
            <div>
              <button className="clinical-action-primary" type="submit">
                Guardar cambios
              </button>
            </div>
          </form>
          {confirm && (
            <ConfirmDialog
              title="Confirmar cambios"
              confirmLabel="Guardar"
              busy={save.isPending}
              onClose={() => setConfirm(false)}
              onConfirm={() => save.mutate(form)}
            >
              <p>¿Confirmas la actualización de los datos de este paciente?</p>
            </ConfirmDialog>
          )}
        </>
      )}
    </>
  );
}

export function BackofficePatientSection() {
  const { id, section } = useParams();
  const [page, setPage] = useState(1);
  const q = useData<Paginated<RecordRow>>(
    `patients/${id}/${section}/?page=${page}`,
  );
  const label = sections.find(([key]) => key === section)?.[1] || "Expediente";
  return (
    <>
      <Link to={`/backoffice/patients/${id}`}>Volver al paciente</Link>
      <div className="workspace-page-header co-mt-4">
        <div>
          <h1>{label}</h1>
          <p className="clinical-page-description">
            Solo lectura · Paciente #{id}
          </p>
        </div>
        {(section === "history" || section === "odontogram") && (
          <Link
            className="clinical-action-outline"
            to={`/backoffice/patients/${id}/${section === "history" ? "edit-history" : "edit-odontogram"}`}
          >
            Editar {label.toLowerCase()}
          </Link>
        )}
      </div>
      <State pending={q.isPending} error={q.error} />
      {q.data && (
        <>
          {q.data.results.length ? (
            <div className="co-grid co-gap-3">
              {q.data.results.map((row) => (
                <section key={row.id} className="workspace-section">
                  <div className="workspace-section-heading">
                    <h2>Registro #{row.id}</h2>
                  </div>
                  <dl className="co-p-4 co-grid co-gap-3">
                    {Object.entries(row)
                      .filter(([key]) => key !== "id")
                      .map(([key, value]) => (
                        <div key={key}>
                          <dt className="co-font-semibold">
                            {key.replaceAll("_", " ")}
                          </dt>
                          <dd className="co-break-words co-whitespace-pre-wrap">
                            <ReadOnlyValue value={value} />
                          </dd>
                        </div>
                      ))}
                  </dl>
                </section>
              ))}
            </div>
          ) : (
            <div className="workspace-empty-state">
              No hay registros en esta sección.
            </div>
          )}
          <Pager page={page} setPage={setPage} data={q.data} />
        </>
      )}
    </>
  );
}

export function BackofficeAppointments() {
  const [params] = useSearchParams();
  const patient = params.get("patient") || "";
  const [page, setPage] = useState(1);
  const [state, setState] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const q = useData<Paginated<Appointment>>(
    `appointments/?${new URLSearchParams({ patient, state, from, to, page: String(page) })}`,
  );
  return (
    <>
      <div className="workspace-page-header">
        <div>
          <h1>Citas</h1>
          <p className="clinical-page-description">
            Agenda global · Solo lectura
          </p>
        </div>
      </div>
      <div className="co-flex co-flex-wrap co-gap-3 co-mb-5">
        <label>
          Desde
          <input
            className="clinical-form-control"
            type="date"
            value={from}
            onChange={(e) => {
              setPage(1);
              setFrom(e.target.value);
            }}
          />
        </label>
        <label>
          Hasta
          <input
            className="clinical-form-control"
            type="date"
            value={to}
            onChange={(e) => {
              setPage(1);
              setTo(e.target.value);
            }}
          />
        </label>
        <label>
          Estado
          <select
            className="clinical-form-control"
            value={state}
            onChange={(e) => {
              setPage(1);
              setState(e.target.value);
            }}
          >
            <option value="">Todos</option>
            <option value="P">Pendiente</option>
            <option value="C">Completada</option>
            <option value="A">Anulada</option>
          </select>
        </label>
      </div>
      <State pending={q.isPending} error={q.error} />
      {q.data && (
        <>
          {q.data.results.length ? (
            <div className="workspace-table-frame">
              <div className="workspace-table-scroll">
                <table className="workspace-data-table">
                  <caption className="co-sr-only">Citas</caption>
                  <thead>
                    <tr>
                      <th>Fecha</th>
                      <th>Paciente</th>
                      <th>Médico</th>
                      <th>Estado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {q.data.results.map((a) => (
                      <tr key={a.id}>
                        <td data-label="Fecha">
                          <Link to={`/backoffice/appointments/${a.id}`}>
                            {a.fecha} {a.hora.slice(0, 5)}
                          </Link>
                        </td>
                        <td data-label="Paciente">
                          <Link to={`/backoffice/patients/${a.patient_id}`}>
                            {a.patient}
                          </Link>
                        </td>
                        <td data-label="Médico">{a.doctor || "Sin asignar"}</td>
                        <td data-label="Estado">
                          {{ P: "Pendiente", C: "Completada", A: "Anulada" }[
                            a.estatus
                          ] || a.estatus}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="workspace-empty-state">
              No hay citas con este filtro.
            </div>
          )}
          <Pager page={page} setPage={setPage} data={q.data} />
        </>
      )}
    </>
  );
}

export function BackofficeAppointment() {
  const toast = useToast();
  const { id } = useParams();
  const q = useData<Appointment>(`appointments/${id}/`);
  const client = useQueryClient();
  const [action, setAction] = useState<"complete" | "cancel" | null>(null);
  const transition = useMutation({
    mutationFn: (operation: "complete" | "cancel") =>
      api(`backoffice/appointments/${id}/${operation}/`, { method: "POST" }),
    onSuccess: async () => {
      setAction(null);
      toast.success("Estado de la cita actualizado.");
      await client.invalidateQueries({ queryKey: ["backoffice"] });
    },
    onError: () => {
      setAction(null);
      toast.error(
        "No fue posible cambiar el estado. La cita puede haber cambiado; actualiza la página.",
      );
    },
  });
  const item = q.data;
  return (
    <>
      <Link to="/backoffice/appointments">Volver a citas</Link>
      <div className="workspace-page-header co-mt-4">
        <div>
          <h1>Cita #{id}</h1>
          <p className="clinical-page-description">Detalle administrativo</p>
        </div>
      </div>
      <State pending={q.isPending} error={q.error} />
      {item && (
        <>
          <dl className="workspace-section co-p-4 co-grid co-gap-3">
            <div>
              <dt>Paciente</dt>
              <dd>
                <Link to={`/backoffice/patients/${item.patient_id}`}>
                  {item.patient}
                </Link>
              </dd>
            </div>
            <div>
              <dt>Médico</dt>
              <dd>{item.doctor || "Sin asignar"}</dd>
            </div>
            <div>
              <dt>Fecha</dt>
              <dd>
                {item.fecha} {item.hora.slice(0, 5)}
              </dd>
            </div>
            <div>
              <dt>Estado</dt>
              <dd>
                {{ P: "Pendiente", C: "Completada", A: "Anulada" }[
                  item.estatus
                ] || item.estatus}
              </dd>
            </div>
          </dl>
          {item.estatus === "P" && (
            <div className="co-flex co-flex-wrap co-gap-3">
              <button
                className="clinical-action-primary"
                onClick={() => setAction("complete")}
              >
                Completar cita
              </button>
              <button
                className="clinical-action-outline"
                onClick={() => setAction("cancel")}
              >
                Cancelar cita
              </button>
            </div>
          )}
          {action && (
            <ConfirmDialog
              title={action === "complete" ? "Completar cita" : "Cancelar cita"}
              confirmLabel={
                action === "complete" ? "Completar" : "Cancelar cita"
              }
              busy={transition.isPending}
              onClose={() => setAction(null)}
              onConfirm={() => transition.mutate(action)}
            >
              <p>¿Confirmas el cambio de estado de esta cita?</p>
            </ConfirmDialog>
          )}
        </>
      )}
    </>
  );
}
