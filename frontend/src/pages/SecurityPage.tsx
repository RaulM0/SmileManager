import { useToast } from "../context/ToastContext";
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, getErrorMessage } from '../api/client';
import { useAuth } from '../context/AuthContext';

type SecuritySession = { id: string; created_at: string; last_seen_at: string; expires_at: string; current: boolean; mfa_verified: boolean };

export default function SecurityPage() {
  const toast = useToast();
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
      toast.success('Sesión cerrada.');
      if (session.current) await logout();
      else setReload((value) => value + 1);
    } catch (reason) { toast.error(getErrorMessage(reason)); }
    finally { setBusy(false); }
  }
  async function saveName() {
    setBusy(true); setError('');
    try { await api('auth/profile/', { method: 'PATCH', body: JSON.stringify(name) }); toast.success('Nombre actualizado. Se utilizará en documentos nuevos.'); }
    catch (reason) { toast.error(getErrorMessage(reason)); }
    finally { setBusy(false); }
  }
  return <main className="workspace-page security-workspace co-mx-auto co-max-w-[1000px]">
    <header className="workspace-page-header">
      <div><h1>Seguridad de mi cuenta</h1><p className="clinical-page-description">Administra tu información profesional y tus sesiones de acceso.</p></div>
      <Link className="clinical-action-outline" to="/"><i className="bi bi-arrow-left" aria-hidden="true" />Volver al espacio de trabajo</Link>
    </header>
    {error && <p className="security-feedback" role="status">{error}</p>}
    <section className="workspace-section" aria-labelledby="account-security-heading">
      <div className="workspace-section-heading"><div><h2 id="account-security-heading">Protección de la cuenta</h2><p>Información sobre tu acceso al sistema</p></div><i className="bi bi-shield-check security-section-icon" aria-hidden="true" /></div>
      <div className="security-section-body">
        <div className="security-factor"><span>Segundo factor</span><strong className={user?.mfa_enabled ? 'security-factor-enabled' : ''}><i className={user?.mfa_enabled ? 'bi bi-check-circle' : 'bi bi-shield'} aria-hidden="true" />{user?.mfa_enabled ? 'Configurado' : 'No configurado'}</strong></div>
        {!user?.mfa_enabled && <p className="clinical-form-help">Obligatorio para cuentas administrativas.</p>}
      </div>
      <p className="workspace-section-note">Las sesiones vencen tras 30 minutos sin solicitudes o a las ocho horas desde el inicio. Cerrar una sesión revoca también sus tokens de acceso.</p>
    </section>
    <section className="workspace-section" aria-labelledby="professional-name-heading">
      <div className="workspace-section-heading"><div><h2 id="professional-name-heading">Nombre del profesional</h2><p>Escribe tu nombre completo para los documentos nuevos.</p></div></div>
      <form className="security-section-body" onSubmit={(event) => { event.preventDefault(); void saveName(); }}>
        <div className="clinical-form-grid">
          <div className="clinical-form-col-6">
            <label className="clinical-form-label" htmlFor="profile-first">Nombre(s)</label>
            <input id="profile-first" autoComplete="given-name" className="clinical-form-control" value={name.first_name} onChange={(event) => setName({ ...name, first_name: event.target.value })} />
          </div>
          <div className="clinical-form-col-6">
            <label className="clinical-form-label" htmlFor="profile-last">Apellidos</label>
            <input id="profile-last" autoComplete="family-name" className="clinical-form-control" value={name.last_name} onChange={(event) => setName({ ...name, last_name: event.target.value })} />
          </div>
        </div>
        <div className="security-form-actions"><button type="submit" className="clinical-action-primary" disabled={busy || !name.first_name.trim() || !name.last_name.trim()}><i className="bi bi-check2" aria-hidden="true" />Guardar nombre</button></div>
      </form>
      <p className="workspace-section-note">Los documentos ya cerrados conservan la identidad registrada al crearlos.</p>
    </section>
    <section className="workspace-section" aria-labelledby="account-sessions-heading">
      <div className="workspace-section-heading"><div><h2 id="account-sessions-heading">Mis sesiones</h2><p>Revisa y cierra los accesos a tu cuenta.</p></div></div>
      <div className="security-session-list">
        {sessions.map((session) => <article key={session.id} className="security-session">
          <div className="security-session-heading"><strong><i className="bi bi-display" aria-hidden="true" />{session.current ? 'Sesión actual' : 'Otra sesión'}</strong><button type="button" disabled={busy} className="clinical-action-outline clinical-action-compact" onClick={() => void revoke(session)}>Cerrar esta sesión</button></div>
          <dl className="security-session-details">
            <div><dt>Inicio</dt><dd><time dateTime={session.created_at}>{new Date(session.created_at).toLocaleString('es-MX')}</time></dd></div>
            <div><dt>Última actividad</dt><dd><time dateTime={session.last_seen_at}>{new Date(session.last_seen_at).toLocaleString('es-MX')}</time></dd></div>
            <div><dt>Segundo factor verificado</dt><dd>{session.mfa_verified ? 'Sí' : 'No'}</dd></div>
          </dl>
        </article>)}
      </div>
      <div className="security-session-footer"><button type="button" className="clinical-action-outline" disabled={busy} onClick={async () => { setBusy(true); try { await api('auth/sessions/revoke-others/', { method: 'POST' }); toast.success('Las otras sesiones se cerraron.'); setReload((value) => value + 1); } catch (reason) { toast.error(getErrorMessage(reason)); } finally { setBusy(false); } }}><i className="bi bi-box-arrow-right" aria-hidden="true" />Cerrar las otras sesiones</button></div>
    </section>
  </main>;
}
