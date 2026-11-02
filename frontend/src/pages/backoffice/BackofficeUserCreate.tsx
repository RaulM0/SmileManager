import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api, ApiError } from '../../api/client';
import { ConfirmDialog } from '../../components/ConfirmDialog';

type CreatedUser = { id: number };
type Fields = { username: string; email: string; first_name: string; last_name: string; password: string; backoffice_access: boolean };
const empty: Fields = { username: '', email: '', first_name: '', last_name: '', password: '', backoffice_access: false };

export function BackofficeUserCreate() {
  const [form, setForm] = useState<Fields>(empty);
  const [confirm, setConfirm] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const create = useMutation({
    mutationFn: () => api<CreatedUser>('backoffice/users/create/', { method: 'POST', body: JSON.stringify(form) }),
    onSuccess: async user => { setConfirm(false); setForm(empty); await queryClient.invalidateQueries({ queryKey: ['backoffice'] }); navigate(`/backoffice/users/${user.id}`); },
    onError: err => {
      setConfirm(false);
      if (err instanceof ApiError && err.status === 400 && err.payload) {
        const messages = Object.entries(err.payload).flatMap(([field, value]) => Array.isArray(value) ? value.map(message => `${field}: ${String(message)}`) : typeof value === 'string' ? [value] : []);
        setError(messages.join(' ') || 'Revisa los datos del usuario.');
      } else setError('No fue posible crear el usuario. Inténtalo de nuevo.');
    },
  });
  function submit(event: FormEvent) { event.preventDefault(); setError(''); setConfirm(true); }
  return <><Link to="/backoffice/users">Volver a usuarios</Link><div className="workspace-page-header co-mt-4"><div><h1>Crear usuario</h1><p className="clinical-page-description">Registra una cuenta para acceder a SmileManager.</p></div></div>
    {error && <div className="workspace-inline-error co-mb-4" role="alert">{error}</div>}
    <form onSubmit={submit} className="workspace-section co-p-5 co-grid co-gap-4 co-max-w-[680px]">
      <label>Usuario <input className="clinical-form-control" required maxLength={150} autoComplete="off" value={form.username} onChange={e => setForm({ ...form, username: e.target.value })} /></label>
      <label>Correo electrónico <input className="clinical-form-control" type="email" required value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} /></label>
      <label>Nombre <input className="clinical-form-control" maxLength={150} value={form.first_name} onChange={e => setForm({ ...form, first_name: e.target.value })} /></label>
      <label>Apellidos <input className="clinical-form-control" maxLength={150} value={form.last_name} onChange={e => setForm({ ...form, last_name: e.target.value })} /></label>
      <label>Contraseña inicial <input className="clinical-form-control" type="password" required maxLength={128} autoComplete="new-password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} /></label>
      <label className="co-flex co-items-start co-gap-2"><input type="checkbox" checked={form.backoffice_access} onChange={e => setForm({ ...form, backoffice_access: e.target.checked })} /> <span>Permitir acceso al Backoffice y a información clínica global</span></label>
      <p className="clinical-form-help">Comparte la contraseña inicial por un canal seguro. El acceso al Backoffice incluye información sensible de todos los pacientes.</p>
      <div><button className="clinical-action-primary" type="submit">Crear usuario</button></div>
    </form>
    {confirm && <ConfirmDialog title="Confirmar creación de usuario" confirmLabel="Crear usuario" busy={create.isPending} onClose={() => setConfirm(false)} onConfirm={() => create.mutate()}><p>Se creará la cuenta {form.username}.{form.backoffice_access && ' Tendrá acceso administrativo a información clínica global.'}</p></ConfirmDialog>}
  </>;
}
