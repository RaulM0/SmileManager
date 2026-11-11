import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api, getErrorMessage } from "../../api/client";
import { ConfirmDialog } from "../../components/ConfirmDialog";
import { AdminState, AdminStatus } from "../../components/workspace/Administration";
import { useAuth } from "../../context/AuthContext";
import type { Paginated } from "../../types/domain";
import { Load, Pages } from "./shared";
import { useAdmin } from "./useAdmin";
import { date } from "./date";
import type { User } from "./types";

export function BackofficeUsers() {
  const [page, setPage] = useState(1);
  const [input, setInput] = useState("");
  const [search, setSearch] = useState("");
  const [state, setState] = useState("");
  const params = new URLSearchParams({ page: String(page), search, state });
  const query = useAdmin<Paginated<User>>(`users/?${params}`);
  function submit(e: FormEvent) {
    e.preventDefault();
    setPage(1);
    setSearch(input);
  }
  return (
    <>
      <div className="workspace-page-header">
        <div>
          <h1>Usuarios</h1>
          <p className="clinical-page-description">
            Administra las cuentas de SmileManager.
          </p>
        </div>
        <Link className="clinical-action-primary" to="/backoffice/users/new">
          <i className="bi bi-person-plus" aria-hidden="true" /> Crear usuario
        </Link>
      </div>
      <form
        onSubmit={submit}
        className="clinical-filter-surface admin-form-grid"
      >
        <label className="clinical-form-label">
          Buscar usuario{" "}
          <input
            className="clinical-form-control"
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
        </label>
        <label className="clinical-form-label">
          Estado{" "}
          <select
            className="clinical-form-control"
            value={state}
            onChange={(e) => {
              setState(e.target.value);
              setPage(1);
            }}
          >
            <option value="">Todos</option>
            <option value="active">Activos</option>
            <option value="inactive">Inactivos</option>
          </select>
        </label>
        <button className="clinical-action-primary co-self-end">Buscar</button>
      </form>
      <Load pending={query.isPending} error={query.error}>
        {query.data && (
          <>
            {query.data.results.length ? (
              <div className="workspace-table-frame">
                <div className="workspace-table-scroll">
                  <table className="workspace-data-table">
                    <thead>
                      <tr>
                        <th>Usuario</th>
                        <th>Correo</th>
                        <th>Estado</th>
                        <th>Acciones</th>
                      </tr>
                    </thead>
                    <tbody>
                      {query.data.results.map((u) => (
                        <tr key={u.id}>
                          <td data-label="Usuario">
                            <span className="co-font-semibold">
                              {u.username}
                            </span>
                          </td>
                          <td data-label="Correo">{u.email || "Sin correo"}</td>
                          <td data-label="Estado">
                            <AdminStatus
                              value={u.is_active ? "ACTIVE" : "INACTIVE"}
                            />
                          </td>
                          <td data-label="Acciones">
                            <Link
                              className="clinical-action-outline clinical-action-compact"
                              to={`/backoffice/users/${u.id}`}
                            >
                              Ver usuario
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <AdminState empty="No hay usuarios con este filtro." />
            )}
            <Pages page={page} setPage={setPage} data={query.data} />
          </>
        )}
      </Load>
    </>
  );
}

export function BackofficeUser() {
  const { id } = useParams();
  const client = useQueryClient();
  const { user: actor } = useAuth();
  const [confirm, setConfirm] = useState(false);
  const [message, setMessage] = useState("");
  const query = useAdmin<User>(`users/${id}/`);
  const u = query.data;
  const mutation = useMutation({
    mutationFn: () =>
      api<User>(
        `backoffice/users/${id}/${u?.is_active ? "deactivate" : "activate"}/`,
        { method: "POST" },
      ),
    onSuccess: async () => {
      setConfirm(false);
      setMessage("Estado actualizado.");
      await client.invalidateQueries({ queryKey: ["backoffice"] });
    },
    onError: (e) => {
      setConfirm(false);
      setMessage(getErrorMessage(e));
    },
  });
  return (
    <>
      <Link to="/backoffice/users">Volver a usuarios</Link>
      <Load pending={query.isPending} error={query.error}>
        {u && (
          <>
            <h1 className="co-text-2xl co-font-semibold co-my-5">
              {u.username}
            </h1>
            {message && (
              <p role="status" className="co-mb-4">
                {message}
              </p>
            )}
            <dl className="clinical-form-surface admin-detail-grid">
              <div>
                <dt>Identificador</dt>
                <dd>{u.id}</dd>
              </div>
              <div>
                <dt>Correo</dt>
                <dd>{u.email || "—"}</dd>
              </div>
              <div>
                <dt>Estado</dt>
                <dd>{u.is_active ? "Activo" : "Inactivo"}</dd>
              </div>
              <div>
                <dt>Staff técnico</dt>
                <dd>{u.is_staff ? "Sí" : "No"}</dd>
              </div>
              <div>
                <dt>Permiso de backoffice asignado</dt>
                <dd>{u.backoffice_assigned ? "Sí" : "No"}</dd>
              </div>
              <div>
                <dt>Creado</dt>
                <dd>{date(u.date_joined)}</dd>
              </div>
              <div>
                <dt>Último acceso</dt>
                <dd>{date(u.last_login)}</dd>
              </div>
            </dl>
            <p className="co-mt-4">
              <Link to={`/backoffice/audit?actor=${u.id}`}>Ver auditoría</Link>
            </p>
            {u.administrative_account && (
              <p className="co-mt-4">
                El estado de esta cuenta administrativa se gestiona fuera del
                backoffice.
              </p>
            )}
            <button
              className="clinical-action-outline co-mt-5"
              disabled={actor?.id === u.id || u.administrative_account}
              onClick={() => setConfirm(true)}
            >
              {u.is_active ? "Desactivar usuario" : "Activar usuario"}
            </button>
            {confirm && (
              <ConfirmDialog
                title={u.is_active ? "Desactivar usuario" : "Activar usuario"}
                confirmLabel={u.is_active ? "Desactivar" : "Activar"}
                busy={mutation.isPending}
                onClose={() => setConfirm(false)}
                onConfirm={() => mutation.mutate()}
              >
                <p>¿Confirmas el cambio de acceso para {u.username}?</p>
              </ConfirmDialog>
            )}
          </>
        )}
      </Load>
    </>
  );
}
