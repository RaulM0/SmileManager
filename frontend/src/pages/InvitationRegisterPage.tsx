import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link, useLocation } from "react-router-dom";
import { api, getErrorMessage } from "../api/client";

export default function InvitationRegisterPage() {
  const token = useLocation().hash.slice(1);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
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
    try {
      await api("clinics/invitations/register/", { method: "POST", body: JSON.stringify({ token, username, password }) });
      window.history.replaceState(window.history.state, "", window.location.pathname);
      setPassword("");
      setCompleted(true);
    } catch (reason) {
      setError(getErrorMessage(reason));
    } finally {
      setBusy(false);
    }
  }

  return <main className="login-workspace"><div className="login-form-panel"><div className="login-form-inner">
    <h1>Crear cuenta por invitación</h1>
    {completed ? <p role="status">Cuenta creada y solicitud aceptada. Ya puedes iniciar sesión.</p> : <>
      <p>El correo de tu cuenta será el que recibió la invitación.</p>
      {invitation && <p>Clínica: <strong>{invitation.clinic}</strong> · Rol: <strong>{invitation.role}</strong></p>}
      {!token && <p role="alert">El enlace no contiene una invitación válida.</p>}
      {error && <p role="alert">{error}</p>}
      <form onSubmit={submit}>
        <label className="clinical-form-label" htmlFor="invitation-username">Usuario</label>
        <input id="invitation-username" className="clinical-form-control" autoComplete="username" maxLength={150} required value={username} onChange={event => setUsername(event.target.value)} />
        <label className="clinical-form-label" htmlFor="invitation-password">Contraseña</label>
        <input id="invitation-password" className="clinical-form-control" type="password" autoComplete="new-password" minLength={8} maxLength={256} required value={password} onChange={event => setPassword(event.target.value)} />
        <button className="clinical-form-submit co-mt-5" disabled={!invitation || busy}>Crear cuenta y aceptar invitación</button>
      </form>
    </>}
    <p><Link to="/login">Iniciar sesión</Link></p>
  </div></div></main>;
}
