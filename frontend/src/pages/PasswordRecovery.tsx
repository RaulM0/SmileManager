import { useToast } from "../context/ToastContext";
import { useEffect, useState } from 'react';
import type { FormEvent, ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { api, ApiError } from '../api/client';

function RecoveryLayout({ children }: { children: ReactNode }) {
  return <div className="login-workspace"><div className="login-shell"><section className="login-context" aria-label="SmileManager"><div className="login-brand"><span className="login-brand-mark"><i className="bi bi-heart-pulse" aria-hidden="true" /></span><strong>SmileManager</strong></div><div className="login-context-copy"><h1>Espacio de trabajo clínico</h1><p>Recupera el acceso a tu cuenta de forma segura.</p></div></section><main className="login-form-panel"><div className="login-form-inner">{children}</div></main></div><p className="login-security-note"><i className="bi bi-shield-check" aria-hidden="true" />Protege tus credenciales de acceso</p></div>;
}

export function ForgotPasswordPage() {
  const toast = useToast();
  const [email, setEmail] = useState(''); const [pending, setPending] = useState(false); const [complete, setComplete] = useState(false);
  async function submit(event: FormEvent) {
    event.preventDefault(); if (pending) return; setPending(true);
    try { await api('auth/password-reset/request/', { method: 'POST', body: JSON.stringify({ email }) }); setComplete(true); toast.success('Solicitud de recuperación procesada. Revisa tu correo.'); }
    catch (err) { toast.error(err instanceof ApiError && err.status === 429 ? 'Demasiados intentos. Espera antes de volver a intentarlo.' : 'No fue posible procesar la solicitud. Inténtalo de nuevo.'); }
    finally { setPending(false); }
  }
  return <RecoveryLayout><h2>Recuperar contraseña</h2>{complete ? <><p role="status">Si existe una cuenta elegible asociada a ese correo, recibirás instrucciones para restablecer tu contraseña.</p><Link className="clinical-action-outline co-mt-5" to="/login">Volver a iniciar sesión</Link></> : <><p>Ingresa el correo asociado a tu cuenta.</p><form onSubmit={submit}><div className="clinical-form-field"><label className="clinical-form-label" htmlFor="recovery-email">Correo electrónico</label><input id="recovery-email" className="clinical-form-control" type="email" autoComplete="email" required maxLength={254} value={email} onChange={e => setEmail(e.target.value)} /></div><button className="clinical-form-submit co-mt-5 co-w-full" disabled={pending}>{pending ? 'Enviando…' : 'Enviar instrucciones'}</button></form><p className="co-mt-4"><Link to="/login">Volver a iniciar sesión</Link></p></>}</RecoveryLayout>;
}

export function ResetPasswordPage() {
  const toast = useToast();
  const [credentials] = useState(() => { const fragment = new URLSearchParams(window.location.hash.slice(1)); return { uid: fragment.get('uid') || '', token: fragment.get('token') || '' }; });
  const [password, setPassword] = useState(''); const [confirmation, setConfirmation] = useState(''); const [show, setShow] = useState(false); const [pending, setPending] = useState(false); const [complete, setComplete] = useState(false); const [invalid, setInvalid] = useState(!credentials.uid || !credentials.token);
  useEffect(() => { if (window.location.hash) window.history.replaceState(window.history.state, '', window.location.pathname + window.location.search); }, []);
  async function submit(event: FormEvent) {
    event.preventDefault(); if (pending) return;
    if (password !== confirmation) { toast.error('Las contraseñas no coinciden.'); return; }
    setPending(true);
    try { await api('auth/password-reset/confirm/', { method: 'POST', body: JSON.stringify({ ...credentials, new_password: password, confirm_password: confirmation }) }); setPassword(''); setConfirmation(''); try { await api('auth/logout/', { method: 'POST' }); } catch { /* The reset succeeded; local credentials must still be cleared. */ } window.dispatchEvent(new Event('smile:auth-expired')); setComplete(true); toast.success('Contraseña restablecida. Ya puedes iniciar sesión.'); }
    catch (err) {
      if (err instanceof ApiError && err.payload?.code === 'invalid_reset') { setInvalid(true); toast.error('Enlace de recuperación inválido. Solicita uno nuevo.'); }
      else if (err instanceof ApiError && Array.isArray(err.payload?.new_password)) toast.error(err.payload.new_password.join(' '));
      else toast.error(err instanceof ApiError && err.status === 429 ? 'Demasiados intentos. Espera antes de volver a intentarlo.' : 'No fue posible cambiar la contraseña. Inténtalo de nuevo.');
    } finally { setPending(false); }
  }
  return <RecoveryLayout><h2>Restablecer contraseña</h2>{complete ? <><p role="status">Tu contraseña se actualizó correctamente.</p><Link className="clinical-action-primary co-mt-5" to="/login">Iniciar sesión</Link></> : invalid ? <><p role="alert">El enlace no es válido, ha caducado o ya fue utilizado.</p><Link to="/forgot-password">Solicitar otro enlace</Link></> : <><p>Elige una contraseña que no sea común ni similar a tus datos personales.</p><p className="clinical-form-help">Usa al menos ocho caracteres; no puede ser completamente numérica.</p><form onSubmit={submit}><div className="clinical-form-field"><label className="clinical-form-label" htmlFor="new-password">Nueva contraseña</label><div className="login-password-field"><input id="new-password" className="clinical-form-control" type={show ? 'text' : 'password'} autoComplete="new-password" required maxLength={128} value={password} onChange={e => setPassword(e.target.value)} /><button type="button" className="login-password-toggle" aria-label={show ? 'Ocultar contraseña' : 'Mostrar contraseña'} aria-pressed={show} onClick={() => setShow(!show)}><i className={`bi bi-eye${show ? '-slash' : ''}`} aria-hidden="true" /></button></div></div><div className="clinical-form-field"><label className="clinical-form-label" htmlFor="confirm-password">Confirmar contraseña</label><input id="confirm-password" className="clinical-form-control" type={show ? 'text' : 'password'} autoComplete="new-password" required maxLength={128} value={confirmation} onChange={e => setConfirmation(e.target.value)} /></div><button className="clinical-form-submit co-mt-5 co-w-full" disabled={pending}>{pending ? 'Guardando…' : 'Restablecer contraseña'}</button></form><p className="co-mt-4"><Link to="/login">Volver a iniciar sesión</Link></p></>}</RecoveryLayout>;
}
