import { useState } from 'react';
import type { FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, getErrorMessage } from '../../api/client';
import { ConfirmDialog } from '../../components/ConfirmDialog';
import { useAuth } from '../../context/AuthContext';
import type { Paginated } from '../../types/domain';

type ClinicStatus = 'ACTIVE' | 'INACTIVE' | 'SUSPENDED';
type Clinic = { id: string; name: string; slug: string; status: ClinicStatus };
type Invitation = { id: string; email: string; expires_at: string };
const labels: Record<ClinicStatus, string> = { ACTIVE: 'Activa', INACTIVE: 'Inactiva', SUSPENDED: 'Suspendida' };

export default function PlatformClinicsPage() {
  const { user } = useAuth();
  const client = useQueryClient();
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<Clinic | null>(null);
  const [change, setChange] = useState<{ clinic: Clinic; status: ClinicStatus } | null>(null);
  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [email, setEmail] = useState('');
  const [replacement, setReplacement] = useState('');
  const [message, setMessage] = useState('');
  const clinics = useQuery({ queryKey: ['platform-clinics', page], enabled: Boolean(user?.is_platform_admin), queryFn: () => api<Paginated<Clinic>>(`backoffice/clinics/?page=${page}`) });
  const invitations = useQuery({ queryKey: ['platform-clinic-invitations', selected?.id], enabled: Boolean(user?.is_platform_admin && selected), queryFn: () => api<Paginated<Invitation>>(`backoffice/clinics/${selected!.id}/initial-admin/`) });
  const mutation = useMutation({
    mutationFn: ({ path, body }: { path: string; body?: object }) => api(path, { method: 'POST', ...(body ? { body: JSON.stringify(body) } : {}) }),
    onSuccess: async () => {
      setMessage('Operación realizada.');
      setChange(null);
      await Promise.all([client.invalidateQueries({ queryKey: ['platform-clinics'] }), client.invalidateQueries({ queryKey: ['platform-clinic-invitations'] })]);
    },
    onError: (error) => { setChange(null); setMessage(getErrorMessage(error)); },
  });
  function create(event: FormEvent) {
    event.preventDefault();
    mutation.mutate({ path: 'backoffice/clinics/', body: { name, slug, status: 'INACTIVE', initial_admin_email: email } }, { onSuccess: () => { setName(''); setSlug(''); setEmail(''); } });
  }
  function invite(event: FormEvent) {
    event.preventDefault();
    if (!selected) return;
    mutation.mutate({ path: `backoffice/clinics/${selected.id}/initial-admin/`, body: { email: replacement } }, { onSuccess: () => setReplacement('') });
  }
  if (!user?.is_platform_admin) return <div role="alert">No tienes permiso para administrar clínicas.</div>;
  return <>
    <div className="workspace-page-header"><div><h1>Clínicas</h1><p className="clinical-page-description">Alta, estado operativo y administración inicial</p></div></div>
    {message && <p role="status">{message}</p>}
    <section className="workspace-section"><h2>Crear clínica</h2><form onSubmit={create} className="co-flex co-flex-wrap co-gap-3 co-mt-3">
      <label>Nombre <input required maxLength={150} value={name} onChange={(event) => setName(event.target.value)} /></label>
      <label>Identificador <input required maxLength={150} pattern="[-a-zA-Z0-9_]+" value={slug} onChange={(event) => setSlug(event.target.value)} /></label>
      <label>Correo del administrador inicial <input required type="email" value={email} onChange={(event) => setEmail(event.target.value)} /></label>
      <button className="clinical-action-primary" disabled={mutation.isPending}>Crear y enviar invitación</button>
    </form><p className="clinical-form-help">La clínica se crea inactiva. Actívala para que el administrador pueda aceptar la invitación.</p></section>
    <section className="workspace-section"><h2>Clínicas registradas</h2>{clinics.isError ? <p role="alert">No fue posible cargar las clínicas.</p> : <div className="workspace-table-scroll"><table className="workspace-data-table"><thead><tr><th>Clínica</th><th>Identificador</th><th>Estado</th><th>Acciones</th></tr></thead><tbody>{clinics.data?.results.map((clinic) => <tr key={clinic.id}><td>{clinic.name}</td><td>{clinic.slug}</td><td>{labels[clinic.status]}</td><td><button type="button" className="clinical-action-outline" onClick={() => { setSelected(clinic); setMessage(''); }}>Administración inicial</button>{clinic.status !== 'ACTIVE' && <button type="button" className="clinical-action-outline" onClick={() => setChange({ clinic, status: 'ACTIVE' })}>Activar</button>}{clinic.status === 'ACTIVE' && <button type="button" className="clinical-action-outline" onClick={() => setChange({ clinic, status: 'SUSPENDED' })}>Suspender</button>}{clinic.status !== 'INACTIVE' && <button type="button" className="clinical-action-outline" onClick={() => setChange({ clinic, status: 'INACTIVE' })}>Desactivar</button>}</td></tr>)}</tbody></table><nav aria-label="Paginación de clínicas"><button disabled={page === 1} onClick={() => setPage(page - 1)}>Anterior</button> Página {page} <button disabled={!clinics.data?.next} onClick={() => setPage(page + 1)}>Siguiente</button></nav></div>}</section>
    {selected && <section className="workspace-section"><h2>Administración inicial: {selected.name}</h2><p>Disponible cuando la clínica no tiene un administrador activo.</p><form onSubmit={invite} className="co-flex co-flex-wrap co-gap-3"><label>Correo de invitación <input required type="email" value={replacement} onChange={(event) => setReplacement(event.target.value)} /></label><button className="clinical-action-outline" disabled={mutation.isPending}>Enviar invitación</button></form>{invitations.isError ? <p role="alert">No fue posible cargar las invitaciones.</p> : <ul>{invitations.data?.results.map((invitation) => <li key={invitation.id}>{invitation.email} · Vence {new Date(invitation.expires_at).toLocaleString('es-MX')} <button type="button" disabled={mutation.isPending} onClick={() => mutation.mutate({ path: `backoffice/clinics/${selected.id}/initial-admin/${invitation.id}/revoke/` })}>Revocar</button></li>)}</ul>}</section>}
    {change && <ConfirmDialog title="Cambiar estado de clínica" confirmLabel="Confirmar cambio" busy={mutation.isPending} onClose={() => setChange(null)} onConfirm={() => mutation.mutate({ path: `backoffice/clinics/${change.clinic.id}/status/`, body: { status: change.status } })}><p>La clínica {change.clinic.name} quedará {labels[change.status].toLowerCase()}.</p></ConfirmDialog>}
  </>;
}
