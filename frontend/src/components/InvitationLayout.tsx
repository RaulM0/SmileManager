import type { ReactNode } from "react";

export default function InvitationLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <div className="login-workspace">
      <div className="login-shell">
        <section className="login-context" aria-label="SmileManager">
          <div className="login-brand">
            <span className="login-brand-mark">
              <i className="bi bi-heart-pulse" aria-hidden="true" />
            </span>
            <strong>SmileManager</strong>
          </div>
          <div className="login-context-copy">
            <h1>Tu equipo, en un solo lugar</h1>
            <p>Únete al espacio de trabajo de tu clínica.</p>
            <ul>
              <li>
                <i className="bi bi-people" aria-hidden="true" />
                Colabora con tu equipo clínico
              </li>
              <li>
                <i className="bi bi-calendar2-check" aria-hidden="true" />
                Gestiona la atención y las citas
              </li>
              <li>
                <i className="bi bi-shield-check" aria-hidden="true" />
                Accede con tu cuenta personal
              </li>
            </ul>
          </div>
        </section>
        <main className="login-form-panel">
          <div className="login-form-inner invitation-content">
            <span className="invitation-heading-icon">
              <i className="bi bi-envelope-open" aria-hidden="true" />
            </span>
            {children}
          </div>
        </main>
      </div>
      <p className="login-security-note">
        <i className="bi bi-shield-check" aria-hidden="true" />
        Acceso exclusivo de personal autorizado
      </p>
    </div>
  );
}
