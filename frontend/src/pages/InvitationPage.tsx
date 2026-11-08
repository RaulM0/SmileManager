import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { api, getErrorMessage } from "../api/client";

export default function InvitationPage() {
  const location = useLocation();
  const token = location.hash.slice(1);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState("");
  const [error, setError] = useState("");
  const [invitation, setInvitation] = useState<{ clinic: string; role: string } | null>(null);

  useEffect(() => {
    if (!token) return;
    let current = true;
    api<{ clinic: string; role: string }>("clinics/invitations/preview/", { method: "POST", body: JSON.stringify({ token }) })
      .then(data => { if (current) setInvitation(data); })
      .catch(reason => { if (current) setError(getErrorMessage(reason)); });
    return () => { current = false; };
  }, [token]);

  async function resolve(action: "accept" | "reject") {
    if (!token || busy) return;
    setBusy(true);
    setError("");
    try {
      await api("clinics/invitations/resolve/", { method: "POST", body: JSON.stringify({ token, action }) });
      window.history.replaceState(window.history.state, "", window.location.pathname);
      setResult(action === "accept" ? "Aceptaste la invitación." : "Rechazaste la invitación.");
    } catch (reason) {
      setError(getErrorMessage(reason));
    } finally {
      setBusy(false);
    }
  }

  return <main className="login-workspace"><div className="login-form-panel"><div className="login-form-inner">
    <h1>Invitación a SmileManager</h1>
    {result ? <p role="status">{result}</p> : <>
      <p>Confirma que iniciaste sesión con el correo al que llegó la invitación.</p>
      {invitation && <p>Clínica: <strong>{invitation.clinic}</strong> · Rol: <strong>{invitation.role}</strong></p>}
      {!token && <p role="alert">El enlace no contiene una invitación válida.</p>}
      {error && <p role="alert">{error}</p>}
      <button className="clinical-form-submit" disabled={!invitation || busy} onClick={() => void resolve("accept")}>Aceptar invitación</button>{" "}
      <button className="clinical-action-outline" disabled={!invitation || busy} onClick={() => void resolve("reject")}>Rechazar</button>
    </>}
    <p><Link to="/">Ir al inicio</Link></p>
  </div></div></main>;
}
