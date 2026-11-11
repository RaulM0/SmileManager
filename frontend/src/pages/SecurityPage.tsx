import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, getErrorMessage } from '../api/client';
import { useAuth } from '../context/AuthContext';

type SecuritySession = { id: string; created_at: string; last_seen_at: string; expires_at: string; current: boolean; mfa_verified: boolean };

export default function SecurityPage() {
  const { user, logout } = useAuth();
  const [sessions, setSessions] = useState<SecuritySession[]>([]);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [reload, setReload] = useState(0);
  const [name, setName] = useState({ first_name: user?.first_name || '', last_name: user?.last_name || '' });
  useEffect(() => { api<SecuritySession[]>('auth/sessions/').then(setSessions).catch((reason) => setError(getErrorMessage(reason))); }, [reload]);
  async function revoke(session: SecuritySession) {
    setBusy(true); setError('');
    try {
      await api(`auth/sessions/${session.id}/revoke/`, { method: 'POST' });
      if (session.current) await logout();
      else setReload((value) => value + 1);
    } catch (reason) { setError(getErrorMessage(reason)); }
    finally { setBusy(false); }
  }
  async function saveName() {
    setBusy(true); setError('');
    try { await api('auth/profile/', { method: 'PATCH', body: JSON.stringify(name) }); setError('Nombre actualizado. Se utilizará en documentos nuevos.'); }
    catch (reason) { setError(getErrorMessage(reason)); }
    finally { setBusy(false); }
  }
  return <main className="workspace-page co-mx-auto co-max-w-[1000px]">
    <Link to="/">Volver al espacio de trabajo</Link><h1>Seguridad de mi cuenta</h1>
    <p>Las sesiones vencen tras 30 minutos sin solicitudes o a las ocho horas desde el inicio. Cerrar una sesión revoca también sus tokens de acceso.</p>
    <p>Segundo factor: {user?.mfa_enabled ? 'Configurado' : 'No configurado; obligatorio para cuentas administrativas'}.</p>
    {error && <p role="status">{error}</p>}
    <section className="workspace-section"><h2>Nombre del profesional</h2><p>Escribe tu nombre completo. Los documentos ya cerrados conservan la identidad registrada al crearlos.</p>
      <label htmlFor="profile-first">Nombre(s)</label><input id="profile-first" className="clinical-form-control" value={name.first_name} onChange={(event) => setName({ ...name, first_name: event.target.value })} />
      <label htmlFor="profile-last">Apellidos</label><input id="profile-last" className="clinical-form-control" value={name.last_name} onChange={(event) => setName({ ...name, last_name: event.target.value })} />
      <button className="clinical-action-primary" disabled={busy || !name.first_name.trim() || !name.last_name.trim()} onClick={() => void saveName()}>Guardar nombre</button>
    </section>
    <section className="workspace-section"><h2>Mis sesiones</h2>
      {sessions.map((session) => <article key={session.id} className="co-mb-4"><strong>{session.current ? 'Sesión actual' : 'Otra sesión'}</strong><p>Inicio: {new Date(session.created_at).toLocaleString('es-MX')} · Última actividad: {new Date(session.last_seen_at).toLocaleString('es-MX')} · MFA: {session.mfa_verified ? 'Sí' : 'No'}</p><button disabled={busy} className="clinical-action-outline" onClick={() => void revoke(session)}>Cerrar esta sesión</button></article>)}
      <button className="clinical-action-outline" disabled={busy} onClick={async () => { setBusy(true); try { await api('auth/sessions/revoke-others/', { method: 'POST' }); setReload((value) => value + 1); } catch (reason) { setError(getErrorMessage(reason)); } finally { setBusy(false); } }}>Cerrar las otras sesiones</button>
    </section>
  </main>;
}
