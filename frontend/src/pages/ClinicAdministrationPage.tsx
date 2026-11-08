import { useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, getClinicContext, getErrorMessage } from "../api/client";
import type { Paginated } from "../types/domain";
import { ConfirmDialog } from "../components/ConfirmDialog";

type Role = "CLINIC_ADMIN" | "DOCTOR" | "STAFF";
type Member = { id: string; username: string; email: string; role: Role; status: string };
type Invitation = { id: string; email: string; role: Role; status: string };
type Event = { id: number; action: string; timestamp: string; actor: string | null };
type Dashboard = { patients: { active: number }; appointments: { today: number; pending: number }; members: { doctors: number; staff: number }; ai: { total: number; failed: number } };
const roles: Array<[Role, string]> = [["DOCTOR", "Médico"], ["STAFF", "Personal"], ["CLINIC_ADMIN", "Administrador de clínica"]];
const roleLabel = (role: Role) => roles.find(([value]) => value === role)?.[1] ?? role;

export default function ClinicAdministrationPage() {
  const clinic = getClinicContext();
  const client = useQueryClient();
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<Role>("DOCTOR");
  const [page, setPage] = useState(1);
  const [message, setMessage] = useState("");
  const [membershipChange, setMembershipChange] = useState<{ member: Member; status: "ACTIVE" | "SUSPENDED" | "REVOKED" } | null>(null);
  const key = [clinic, "clinic-admin"];
  const dashboard = useQuery({ queryKey: [...key, "dashboard"], queryFn: () => api<Dashboard>("clinics/admin/dashboard/") });
  const members = useQuery({ queryKey: [...key, "members", page], queryFn: () => api<Paginated<Member>>(`clinics/admin/memberships/?page=${page}`) });
  const invitations = useQuery({ queryKey: [...key, "invitations"], queryFn: () => api<Paginated<Invitation>>("clinics/admin/invitations/") });
  const events = useQuery({ queryKey: [...key, "audit"], queryFn: () => api<Paginated<Event>>("clinics/admin/audit/?page_size=5") });
  const mutation = useMutation({
    mutationFn: ({ path, method, body }: { path: string; method: string; body?: object }) => api(path, { method, ...(body ? { body: JSON.stringify(body) } : {}) }),
    onSuccess: async () => { setMembershipChange(null); setMessage("Operación realizada."); await client.invalidateQueries({ queryKey: key }); },
    onError: (error) => { setMembershipChange(null); setMessage(getErrorMessage(error)); },
  });
  function invite(event: FormEvent) {
    event.preventDefault();
    mutation.mutate({ path: "clinics/invitations/", method: "POST", body: { email, role } }, { onSuccess: () => setEmail("") });
  }
  return <div className="workspace-page co-mx-auto co-max-w-[1320px]">
    <div className="workspace-page-header"><div><h1>Administración de la clínica</h1><p className="clinical-page-description">Personal, invitaciones y actividad de la organización</p></div></div>
    {message && <p role="status">{message}</p>}
    {dashboard.isError ? <p role="alert">No fue posible cargar el resumen.</p> : dashboard.data && <div className="workspace-summary-strip" aria-label="Resumen de clínica">{[["Pacientes activos", dashboard.data.patients.active], ["Citas hoy", dashboard.data.appointments.today], ["Médicos", dashboard.data.members.doctors], ["Personal", dashboard.data.members.staff], ["Análisis de IA", dashboard.data.ai.total], ["Fallos de IA", dashboard.data.ai.failed]].map(([label, value]) => <div key={label}><span>{label}</span><strong>{value}</strong></div>)}</div>}
    <section className="workspace-section"><h2>Invitar personal</h2><form onSubmit={invite} className="co-flex co-flex-wrap co-gap-3 co-mt-3"><label>Correo electrónico <input type="email" value={email} required onChange={(event) => setEmail(event.target.value)} /></label><label>Rol <select value={role} onChange={(event) => setRole(event.target.value as Role)}>{roles.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label><button className="clinical-action-primary" disabled={mutation.isPending}>Enviar invitación</button></form></section>
    <section className="workspace-section"><h2>Personal</h2>{members.isError ? <p role="alert">No fue posible cargar el personal.</p> : <div className="workspace-table-scroll"><table className="workspace-data-table"><thead><tr><th>Usuario</th><th>Rol</th><th>Estado</th><th>Acciones</th></tr></thead><tbody>{members.data?.results.map((member) => <tr key={member.id}><td>{member.username}<br /><small>{member.email}</small></td><td><select aria-label={`Rol de ${member.username}`} value={member.role} disabled={mutation.isPending || member.status === "REVOKED"} onChange={(event) => mutation.mutate({ path: `clinics/memberships/${member.id}/`, method: "PATCH", body: { role: event.target.value } })}>{roles.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></td><td>{member.status}</td><td>{member.status === "REVOKED" ? <span>Requiere una nueva invitación</span> : <><button type="button" className="clinical-action-outline" disabled={mutation.isPending} onClick={() => setMembershipChange({ member, status: member.status === "ACTIVE" ? "SUSPENDED" : "ACTIVE" })}>{member.status === "ACTIVE" ? "Suspender" : "Reactivar"}</button><button type="button" className="clinical-action-outline" disabled={mutation.isPending} onClick={() => setMembershipChange({ member, status: "REVOKED" })}>Revocar</button></>}</td></tr>)}</tbody></table><nav aria-label="Paginación de personal"><button disabled={page === 1} onClick={() => setPage(page - 1)}>Anterior</button> Página {page} <button disabled={!members.data?.next} onClick={() => setPage(page + 1)}>Siguiente</button></nav></div>}</section>
    <section className="workspace-section"><h2>Invitaciones recientes</h2>{invitations.isError ? <p role="alert">No fue posible cargar las invitaciones.</p> : <ul>{invitations.data?.results.map((invitation) => <li key={invitation.id}>{invitation.email} · {roleLabel(invitation.role)} · {invitation.status} {invitation.status === "PENDING" && <button type="button" disabled={mutation.isPending} onClick={() => mutation.mutate({ path: `clinics/invitations/${invitation.id}/revoke/`, method: "POST" })}>Revocar</button>}</li>)}</ul>}</section>
    <section className="workspace-section"><h2>Actividad reciente</h2>{events.isError ? <p role="alert">No fue posible cargar la actividad.</p> : <ul>{events.data?.results.map((event) => <li key={event.id}>{event.action} · {event.actor ?? "Sistema"} · {new Date(event.timestamp).toLocaleString("es-MX")}</li>)}</ul>}</section>
    {membershipChange && <ConfirmDialog title="Cambiar acceso" confirmLabel="Confirmar cambio" busy={mutation.isPending} onClose={() => setMembershipChange(null)} onConfirm={() => mutation.mutate({ path: `clinics/memberships/${membershipChange.member.id}/`, method: "PATCH", body: { status: membershipChange.status } })}><p>Se cambiará el acceso de {membershipChange.member.username}. {membershipChange.status === "REVOKED" && "Para volver a entrar necesitará aceptar una nueva invitación."}</p></ConfirmDialog>}
  </div>;
}
