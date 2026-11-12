import { useToast } from "../context/ToastContext";
import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import InvitationLayout from "../components/InvitationLayout";
import { invitationRoleLabel } from "../utils/invitations";
import { api, getErrorMessage } from "../api/client";

export default function InvitationPage() {
  const toast = useToast();
  const location = useLocation();
  const token = location.hash.slice(1);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState("");
  const [error, setError] = useState("");
  const [invitation, setInvitation] = useState<{
    clinic: string;
    role: string;
  } | null>(null);

  useEffect(() => {
    if (!token) return;
    let current = true;
    api<{ clinic: string; role: string }>("clinics/invitations/preview/", {
      method: "POST",
      body: JSON.stringify({ token }),
    })
      .then((data) => {
        if (current) setInvitation(data);
      })
      .catch((reason) => {
        if (current) setError(getErrorMessage(reason));
      });
    return () => {
      current = false;
    };
  }, [token]);

  async function resolve(action: "accept" | "reject") {
    if (!token || busy) return;
    setBusy(true);
    setError("");
    try {
      await api("clinics/invitations/resolve/", {
        method: "POST",
        body: JSON.stringify({ token, action }),
      });
      window.history.replaceState(
        window.history.state,
        "",
        window.location.pathname,
      );
      toast.success(
        action === "accept"
          ? "Aceptaste la invitación."
          : "Rechazaste la invitación.",
      );
      setResult(
        action === "accept"
          ? "Aceptaste la invitación."
          : "Rechazaste la invitación.",
      );
    } catch (reason) {
      toast.error(getErrorMessage(reason));
    } finally {
      setBusy(false);
    }
  }

  return (
    <InvitationLayout>
      <h2>Invitación a SmileManager</h2>
      {result ? (
        <div className="invitation-result">
          <i className="bi bi-check-circle" aria-hidden="true" />
          <p>{result}</p>
        </div>
      ) : (
        <>
          <p>
            Confirma que iniciaste sesión con el correo al que llegó la
            invitación.
          </p>
          {invitation && (
            <dl className="invitation-details">
              <div>
                <dt>Clínica</dt>
                <dd>{invitation.clinic}</dd>
              </div>
              <div>
                <dt>Rol asignado</dt>
                <dd>{invitationRoleLabel(invitation.role)}</dd>
              </div>
            </dl>
          )}
          {(!token || error) && (
            <div className="invitation-notice" role="alert">
              <i className="bi bi-info-circle" aria-hidden="true" />
              <div>
                <p>{error || "El enlace no contiene una invitación válida."}</p>
                {!invitation && (
                  <span>
                    Solicita a la administración de la clínica una nueva
                    invitación.
                  </span>
                )}
              </div>
            </div>
          )}
          {token && !invitation && !error && (
            <p className="clinical-form-help" role="status">
              Consultando invitación…
            </p>
          )}
          <div className="invitation-actions">
            <button
              className="clinical-form-submit"
              disabled={!invitation || busy}
              onClick={() => void resolve("accept")}
            >
              {busy ? (
                <span className="clinical-form-spinner" aria-hidden="true" />
              ) : (
                <i className="bi bi-check2" aria-hidden="true" />
              )}
              Aceptar invitación
            </button>
            <button
              className="clinical-action-outline"
              disabled={!invitation || busy}
              onClick={() => void resolve("reject")}
            >
              Rechazar
            </button>
          </div>
        </>
      )}
      <div className="invitation-footer">
        <Link className="clinical-action-outline" to="/">
          <i className="bi bi-arrow-left" aria-hidden="true" />
          Ir al inicio
        </Link>
      </div>
    </InvitationLayout>
  );
}
