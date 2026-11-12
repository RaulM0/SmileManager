import { useToast } from "../context/ToastContext";
import { auditActionLabel } from "../utils/auditLabels";
import { Link } from 'react-router-dom';
import {
  AdminSection,
  AdminState,
  AdminStatus,
  AdminPagination,
} from "../components/workspace/Administration";
import { useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, getClinicContext, getErrorMessage } from "../api/client";
import type { Paginated } from "../types/domain";
import { ConfirmDialog } from "../components/ConfirmDialog";

type Role = "CLINIC_ADMIN" | "DOCTOR" | "STAFF";
type Member = {
  id: string;
  username: string;
  email: string;
  role: Role;
  status: string;
};
type Invitation = { id: string; email: string; role: Role; status: string };
type Event = {
  id: number;
  action: string;
  timestamp: string;
  actor: string | null;
};
type Dashboard = {
  patients: { active: number };
  appointments: { today: number; pending: number };
  members: { doctors: number; staff: number };
  ai: { total: number; failed: number };
};
const roles: Array<[Role, string]> = [
  ["DOCTOR", "Médico"],
  ["STAFF", "Personal"],
  ["CLINIC_ADMIN", "Administrador de clínica"],
];
const roleLabel = (role: Role) =>
  roles.find(([value]) => value === role)?.[1] ?? role;

export default function ClinicAdministrationPage({ aiEnabled = false }: { aiEnabled?: boolean }) {
  const toast = useToast();
  const clinic = getClinicContext();
  const client = useQueryClient();
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<Role>("DOCTOR");
  const [page, setPage] = useState(1);
  const [membershipChange, setMembershipChange] = useState<{
    member: Member;
    status: "ACTIVE" | "SUSPENDED" | "REVOKED";
  } | null>(null);
  const key = [clinic, "clinic-admin"];
  const dashboard = useQuery({
    queryKey: [...key, "dashboard"],
    queryFn: () => api<Dashboard>("clinics/admin/dashboard/"),
  });
  const members = useQuery({
    queryKey: [...key, "members", page],
    queryFn: () =>
      api<Paginated<Member>>(`clinics/admin/memberships/?page=${page}`),
  });
  const invitations = useQuery({
    queryKey: [...key, "invitations"],
    queryFn: () => api<Paginated<Invitation>>("clinics/admin/invitations/"),
  });
  const events = useQuery({
    queryKey: [...key, "audit"],
    queryFn: () => api<Paginated<Event>>("clinics/admin/audit/?page_size=5"),
  });
  const mutation = useMutation({
    mutationFn: ({
      path,
      method,
      body,
    }: {
      path: string;
      method: string;
      body?: object;
    }) =>
      api(path, { method, ...(body ? { body: JSON.stringify(body) } : {}) }),
    onSuccess: async () => {
      setMembershipChange(null);
      toast.success("Operación realizada.");
      await client.invalidateQueries({ queryKey: key });
    },
    onError: (error) => {
      setMembershipChange(null);
      toast.error(getErrorMessage(error));
    },
  });
  function invite(event: FormEvent) {
    event.preventDefault();
    mutation.mutate(
      { path: "clinics/invitations/", method: "POST", body: { email, role } },
      { onSuccess: () => setEmail("") },
    );
  }
  return (
    <div className="workspace-page co-mx-auto co-max-w-[1320px]">
      <div className="workspace-page-header">
        <div>
          <h1>Administración de la clínica</h1>
          <Link to="/compliance">Configurar privacidad y consentimientos</Link>
          <p className="clinical-page-description">
            Personal, invitaciones y actividad de la organización
          </p>
        </div>
      </div>
      {dashboard.isPending ? (
        <AdminState pending />
      ) : dashboard.isError ? (
        <AdminState error />
      ) : (
        dashboard.data && (
          <div
            className="workspace-summary-strip admin-summary-strip"
            aria-label="Resumen de clínica"
          >
            {[
              ["Pacientes activos", dashboard.data.patients.active],
              ["Citas hoy", dashboard.data.appointments.today],
              ["Médicos", dashboard.data.members.doctors],
              ["Personal", dashboard.data.members.staff],
              ...(aiEnabled ? [["Análisis de IA", dashboard.data.ai.total], ["Fallos de IA", dashboard.data.ai.failed]] : []),
            ].map(([label, value]) => (
              <div key={label}>
                <span>{label}</span>
                <strong>{value}</strong>
              </div>
            ))}
          </div>
        )
      )}
      <AdminSection
        title="Invitar personal"
        description="Envía una invitación y elige los permisos que tendrá la persona en esta clínica."
      >
        <form onSubmit={invite} className="clinical-form-body admin-form-grid">
          <label className="clinical-form-label">
            Correo electrónico{" "}
            <input
              className="clinical-form-control"
              type="email"
              value={email}
              required
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>
          <label className="clinical-form-label">
            Rol{" "}
            <select
              className="clinical-form-control"
              value={role}
              onChange={(event) => setRole(event.target.value as Role)}
            >
              {roles.map(([value, label]) => (
                <option value={value} key={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <button
            className="clinical-action-primary"
            disabled={mutation.isPending}
          >
            Enviar invitación
          </button>
        </form>
      </AdminSection>
      <AdminSection
        title="Personal"
        description="Gestiona los roles y el acceso de los integrantes de tu clínica."
      >
        {members.isPending ? (
          <AdminState pending />
        ) : members.isError ? (
          <AdminState error />
        ) : !members.data?.results.length ? (
          <AdminState empty="No hay personal registrado." />
        ) : (
          <div className="workspace-table-scroll">
            <table className="workspace-data-table">
              <thead>
                <tr>
                  <th>Usuario</th>
                  <th>Rol</th>
                  <th>Estado</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {members.data?.results.map((member) => (
                  <tr key={member.id}>
                    <td data-label="Usuario">
                      {member.username}
                      <br />
                      <small>{member.email}</small>
                    </td>
                    <td data-label="Rol">
                      <select
                        className="clinical-form-control"
                        aria-label={`Rol de ${member.username}`}
                        value={member.role}
                        disabled={
                          mutation.isPending || member.status === "REVOKED"
                        }
                        onChange={(event) =>
                          mutation.mutate({
                            path: `clinics/memberships/${member.id}/`,
                            method: "PATCH",
                            body: { role: event.target.value },
                          })
                        }
                      >
                        {roles.map(([value, label]) => (
                          <option key={value} value={value}>
                            {label}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td data-label="Estado">
                      <AdminStatus value={member.status} />
                    </td>
                    <td data-label="Acciones" className="admin-table-actions">
                      {member.status === "REVOKED" ? (
                        <span>Requiere una nueva invitación</span>
                      ) : (
                        <>
                          <button
                            type="button"
                            className="clinical-action-outline"
                            disabled={mutation.isPending}
                            onClick={() =>
                              setMembershipChange({
                                member,
                                status:
                                  member.status === "ACTIVE"
                                    ? "SUSPENDED"
                                    : "ACTIVE",
                              })
                            }
                          >
                            {member.status === "ACTIVE"
                              ? "Suspender"
                              : "Reactivar"}
                          </button>
                          <button
                            type="button"
                            className="clinical-action-outline"
                            disabled={mutation.isPending}
                            onClick={() =>
                              setMembershipChange({ member, status: "REVOKED" })
                            }
                          >
                            Revocar
                          </button>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <AdminPagination
              label="Paginación de personal"
              page={page}
              count={members.data?.count}
              next={members.data?.next}
              busy={members.isFetching}
              onPage={setPage}
            />
          </div>
        )}
      </AdminSection>
      <AdminSection title="Invitaciones recientes">
        {invitations.isPending ? (
          <AdminState pending />
        ) : invitations.isError ? (
          <AdminState error />
        ) : !invitations.data?.results.length ? (
          <AdminState empty="No hay invitaciones recientes." />
        ) : (
          <ul className="admin-activity-list">
            {invitations.data?.results.map((invitation) => (
              <li key={invitation.id}>
                {invitation.email} · {roleLabel(invitation.role)} ·{" "}
                <AdminStatus value={invitation.status} />{" "}
                {invitation.status === "PENDING" && (
                  <button
                    type="button"
                    className="clinical-action-danger clinical-action-compact"
                    disabled={mutation.isPending}
                    onClick={() =>
                      mutation.mutate({
                        path: `clinics/invitations/${invitation.id}/revoke/`,
                        method: "POST",
                      })
                    }
                  >
                    Revocar
                  </button>
                )}
              </li>
            ))}
          </ul>
        )}
      </AdminSection>
      <AdminSection title="Actividad reciente">
        {events.isPending ? (
          <AdminState pending />
        ) : events.isError ? (
          <AdminState error />
        ) : !events.data?.results.length ? (
          <AdminState empty="Aún no hay actividad registrada." />
        ) : (
          <ul className="admin-activity-list">
            {events.data?.results.map((event) => (
              <li key={event.id}>
                <div className="co-flex co-flex-wrap co-items-start co-justify-between co-gap-2">
                  <div><strong>{auditActionLabel(event.action)}</strong><p className="co-m-0 co-text-xs co-text-clinical-muted">{event.actor ? `Realizado por ${event.actor}` : "Actividad automática del sistema"}</p></div>
                  <time className="co-text-xs co-text-clinical-muted" dateTime={event.timestamp}>{new Date(event.timestamp).toLocaleString("es-MX", { dateStyle: "medium", timeStyle: "short" })}</time>
                </div>
              </li>
            ))}
          </ul>
        )}
      </AdminSection>
      {membershipChange && (
        <ConfirmDialog
          title="Cambiar acceso"
          confirmLabel="Confirmar cambio"
          busy={mutation.isPending}
          onClose={() => setMembershipChange(null)}
          onConfirm={() =>
            mutation.mutate({
              path: `clinics/memberships/${membershipChange.member.id}/`,
              method: "PATCH",
              body: { status: membershipChange.status },
            })
          }
        >
          <p>
            Se cambiará el acceso de {membershipChange.member.username}.{" "}
            {membershipChange.status === "REVOKED" &&
              "Para volver a entrar necesitará aceptar una nueva invitación."}
          </p>
        </ConfirmDialog>
      )}
    </div>
  );
}
