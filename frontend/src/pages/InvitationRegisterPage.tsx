import { useToast } from "../context/ToastContext";
import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link, useLocation } from "react-router-dom";
import { api, getErrorMessage, getFormErrors } from "../api/client";

import InvitationLayout from "../components/InvitationLayout";
import { invitationRoleLabel } from "../utils/invitations";

export default function InvitationRegisterPage() {
  const toast = useToast();
  const token = useLocation().hash.slice(1);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [completed, setCompleted] = useState(false);
  const [error, setError] = useState("");
  const [invitation, setInvitation] = useState<{ clinic: string; role: string } | null>(null);

  useEffect(() => {
    if (!token) return;
    let current = true;
    api<{ clinic: string; role: string }>("clinics/invitations/register/preview/", { method: "POST", body: JSON.stringify({ token }) })
      .then(data => { if (current) setInvitation(data); })
      .catch(reason => { if (current) setError(getErrorMessage(reason)); });
    return () => { current = false; };
  }, [token]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || busy) return;
    setBusy(true);
    setError("");
    setFieldErrors({});
    try {
      await api("clinics/invitations/register/", { method: "POST", body: JSON.stringify({ token, username, password }) });
      window.history.replaceState(window.history.state, "", window.location.pathname);
      setPassword("");
      setCompleted(true);
      toast.success("Cuenta creada y solicitud aceptada. Ya puedes iniciar sesión.");
    } catch (reason) {
      const errors = getFormErrors<'username' | 'password'>(reason);
      const text = (value: unknown) => Array.isArray(value) ? value.join(' ') : typeof value === 'string' ? value : '';
      setFieldErrors({ username: text(errors.username), password: text(errors.password) });
      toast.error(text(errors.detail) || (errors.username || errors.password ? '' : getErrorMessage(reason)));
    } finally {
      setBusy(false);
    }
  }

  return <InvitationLayout>
    <h2>Crear cuenta por invitación</h2>
    {completed ? <div className="invitation-result"><i className="bi bi-check-circle" aria-hidden="true" /><p>Cuenta creada y solicitud aceptada. Ya puedes iniciar sesión.</p></div> : <>
      <p>El correo de tu cuenta será el que recibió la invitación.</p>
      {invitation && <dl className="invitation-details"><div><dt>Clínica</dt><dd>{invitation.clinic}</dd></div><div><dt>Rol asignado</dt><dd>{invitationRoleLabel(invitation.role)}</dd></div></dl>}
      {!token && <div className="invitation-notice" role="alert">El enlace no contiene una invitación válida.</div>}
      {error && <div className="clinical-form-alert co-mb-4" role="alert">{error}</div>}
      {token && !invitation && !error && <p className="clinical-form-help" role="status">Consultando invitación…</p>}
      <form onSubmit={submit}>
        <div className="clinical-form-field">
          <label className="clinical-form-label" htmlFor="invitation-username">Usuario</label>
          <input id="invitation-username" className="clinical-form-control" autoComplete="username" maxLength={150} required value={username} aria-invalid={Boolean(fieldErrors.username)} aria-describedby={fieldErrors.username ? 'invitation-username-error' : undefined} onChange={event => setUsername(event.target.value)} />
          {fieldErrors.username && <span id="invitation-username-error" className="clinical-form-field-error" role="alert">{fieldErrors.username}</span>}
        </div>
        <div className="clinical-form-field">
          <label className="clinical-form-label" htmlFor="invitation-password">Contraseña</label>
          <div className="login-password-field">
            <input id="invitation-password" className="clinical-form-control" type={showPassword ? 'text' : 'password'} autoComplete="new-password" minLength={8} maxLength={256} required value={password} aria-invalid={Boolean(fieldErrors.password)} aria-describedby={fieldErrors.password ? 'invitation-password-help invitation-password-error' : 'invitation-password-help'} onChange={event => setPassword(event.target.value)} />
            <button type="button" className="login-password-toggle" aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'} aria-pressed={showPassword} onClick={() => setShowPassword(!showPassword)}><i className={showPassword ? 'bi bi-eye-slash' : 'bi bi-eye'} aria-hidden="true" /></button>
          </div>
          <span id="invitation-password-help" className="clinical-form-help">Usa al menos 8 caracteres. Evita contraseñas comunes, solo números o similares a tu usuario o correo.</span>
          {fieldErrors.password && <span id="invitation-password-error" className="clinical-form-field-error" role="alert">{fieldErrors.password}</span>}
        </div>
        <button className="clinical-form-submit co-mt-5 co-w-full" disabled={!invitation || busy}>{busy ? <><span className="clinical-form-spinner" aria-hidden="true" />Creando cuenta…</> : 'Crear cuenta y aceptar invitación'}</button>
      </form>
    </>}
    <div className="invitation-footer"><Link className="clinical-action-outline" to="/login"><i className="bi bi-box-arrow-in-right" aria-hidden="true" />Iniciar sesión</Link></div>
  </InvitationLayout>;
}
