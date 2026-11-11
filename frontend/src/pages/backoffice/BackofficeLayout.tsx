import { useEffect, useRef, useState } from "react";
import { Link, NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

const nav = [
  ["Resumen", "/backoffice", "bi-grid-1x2"],
  ["Usuarios", "/backoffice/users", "bi-people"],
  ["Auditoría", "/backoffice/audit", "bi-journal-text"],
  ["IA", "/backoffice/ai", "bi-cpu"],
  ["Sistema", "/backoffice/system", "bi-hdd-network"],
];
export function BackofficeLayout() {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const toggleRef = useRef<HTMLButtonElement>(null);
  const sidebarRef = useRef<HTMLElement>(null);
  useEffect(() => {
    if (!open) return undefined;
    sidebarRef.current?.querySelector<HTMLElement>("a[href]")?.focus();
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
        toggleRef.current?.focus();
        return;
      }
      if (event.key !== "Tab") return;
      const links = sidebarRef.current?.querySelectorAll<HTMLElement>(
        "a[href], button:not(:disabled)",
      );
      if (!links?.length) return;
      if (event.shiftKey && document.activeElement === links[0]) {
        event.preventDefault();
        links[links.length - 1].focus();
      } else if (
        !event.shiftKey &&
        document.activeElement === links[links.length - 1]
      ) {
        event.preventDefault();
        links[0].focus();
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open]);
  if (!user?.can_access_backoffice)
    return (
      <main className="co-p-8">
        <h1>Acceso no autorizado</h1>
        <p>No tienes permiso para acceder a esta sección.</p>
        <Link to="/">Volver al inicio</Link>
      </main>
    );
  return (
    <div className="app-shell workspace-shell">
      <a className="skip-link" href="#backoffice-content">
        Saltar al contenido
      </a>
      <header className="workspace-topbar">
        <button
          ref={toggleRef}
          className="workspace-menu-toggle"
          type="button"
          aria-controls="backoffice-nav"
          aria-expanded={open}
          aria-label={open ? "Cerrar navegación" : "Abrir navegación"}
          onClick={() => setOpen((value) => !value)}
        >
          <i
            className={`bi ${open ? "bi-x-lg" : "bi-list"}`}
            aria-hidden="true"
          />
        </button>
        <Link
          className="workspace-brand co-flex co-items-center"
          to="/backoffice"
        >
          <span className="workspace-brand-mark" aria-hidden="true">
            <i className="bi bi-heart-pulse-fill" />
          </span>
          <span>SmileManager</span>
        </Link>
        <div className="workspace-context">Administración del sistema</div>
        <div className="workspace-user">
          <span className="workspace-user-avatar" aria-hidden="true">
            {user.username.slice(0, 1).toUpperCase()}
          </span>
          <span className="workspace-user-name">{user.username}</span>
          <Link className="workspace-logout" to="/">
            <i className="bi bi-arrow-left" aria-hidden="true" />
            <span>Ir a la aplicación</span>
          </Link>
        </div>
      </header>
      {open && (
        <button
          type="button"
          className="workspace-scrim"
          aria-label="Cerrar navegación"
          onClick={() => {
            setOpen(false);
            toggleRef.current?.focus();
          }}
        />
      )}
      <div className="workspace-body">
        <aside
          ref={sidebarRef}
          id="backoffice-nav"
          className={`workspace-sidebar${open ? " is-open" : ""}`}
          role={open ? "dialog" : undefined}
          aria-modal={open ? "true" : undefined}
          aria-label="Navegación administrativa"
        >
          <nav aria-label="Administración">
            <div className="workspace-nav-group">
              <div className="workspace-nav-label">ADMINISTRACIÓN</div>
              {[
                ...nav.filter(([, url]) => url !== "/backoffice/ai" || user.ai_globally_enabled),
                ...(user.is_platform_admin
                  ? [["Clínicas", "/backoffice/clinics", "bi-building"]]
                  : []),
              ].map(([label, url, icon]) => (
                <NavLink
                  end={url === "/backoffice"}
                  key={url}
                  to={url}
                  onClick={() => {
                    setOpen(false);
                    toggleRef.current?.focus();
                  }}
                  className={({ isActive }) =>
                    `workspace-nav-link${isActive ? " is-active" : ""}`
                  }
                >
                  <i className={`bi ${icon}`} aria-hidden="true" />
                  <span>{label}</span>
                </NavLink>
              ))}
            </div>
          </nav>
          <div className="workspace-sidebar-footer">
            <span className="workspace-clinic-mark" aria-hidden="true">
              SM
            </span>
            <span>
              SmileManager
              <br />
              <small>Administración del sistema</small>
            </span>
          </div>
        </aside>
        <main
          id="backoffice-content"
          className="workspace-main co-min-w-0"
          tabIndex={-1}
        >
          <div className="workspace-page co-mx-auto co-w-full co-max-w-[1320px]">
            <Outlet />
          </div>
          <footer className="workspace-footer">
            <span>SmileManager</span>
            <Link to="/privacy">Aviso de Privacidad</Link>
          </footer>
        </main>
      </div>
    </div>
  );
}
