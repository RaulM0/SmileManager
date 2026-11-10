import { useEffect, useRef, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import PatientWorkspaceNav from "../components/patients/PatientWorkspaceNav";
import { useToast } from "../context/ToastContext";
import { getErrorMessage } from "../api/client";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { discardDraftsFor, hasUnsavedChanges } from "../hooks/useUnsavedChanges";
import type { ClinicOption } from "./ClinicWorkspace";
import ClinicAdministrationPage from "../pages/ClinicAdministrationPage";
import StaffAgendaPage from "../pages/StaffAgendaPage";

const navigation: Array<{ label: string; items: Array<[string, string, string, boolean]> }> = [
  {
    label: "OPERACIÓN",
    items: [
      ["Inicio", "/", "bi-grid-1x2", true],
      ["Citas", "/appointments", "bi-calendar3", false],
    ],
  },
  {
    label: "ATENCIÓN CLÍNICA",
    items: [
      ["Pacientes", "/patients", "bi-people", false],
      ["Diagnósticos", "/diagnostics", "bi-image", false],
    ],
  },
  {
    label: "ADMINISTRACIÓN",
    items: [["Exportaciones", "/exports", "bi-download", false]],
  },
];

export default function AppLayout({ clinics = [], activeClinic = null, onClinicChange, clinicBusy = false }: { clinics?: ClinicOption[]; activeClinic?: ClinicOption | null; onClinicChange?: (id: string) => void; clinicBusy?: boolean }) {
  const { user, logout } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const location = useLocation();
  const patientMatch = location.pathname.match(/^\/patients\/(\d+)(?:\/|$)/);
  const [menuOpen, setMenuOpen] = useState(false);
  const [confirmLogout, setConfirmLogout] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);
  const menuToggleRef = useRef<HTMLButtonElement>(null);
  const sidebarRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (!menuOpen) return undefined;
    sidebarRef.current?.querySelector<HTMLElement>("a[href]")?.focus();
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setMenuOpen(false);
        menuToggleRef.current?.focus();
        return;
      }
      if (event.key !== "Tab") return;
      const focusable = sidebarRef.current?.querySelectorAll<HTMLElement>("a[href], button:not(:disabled)");
      if (!focusable?.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [menuOpen]);

  async function handleLogout() {
    if (hasUnsavedChanges()) { setConfirmLogout(true); return; }
    await finishLogout();
  }

  async function finishLogout() {
    if (loggingOut) return;
    setLoggingOut(true);
    try {
      await discardDraftsFor(logout);
      navigate("/login", { replace: true });
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      setLoggingOut(false);
    }
  }

  function renderNavigation() {
    const groups = !activeClinic || activeClinic.role !== "DOCTOR" ? [{ label: "CLÍNICA", items: [["Inicio", "/", "bi-grid-1x2", true] as [string, string, string, boolean]] }] : navigation;
    const visibleGroups = groups.map((group) => ({ ...group, items: group.items.filter(([, to]) => to !== "/diagnostics" || activeClinic?.ai_effective) })).filter((group) => group.items.length);
    return [...visibleGroups, ...(user?.can_access_backoffice ? [{ label: "SISTEMA", items: [["Administración", "/backoffice", "bi-shield-lock", false] as [string, string, string, boolean]] }] : [])].map((group) => (
      <div className="workspace-nav-group" key={group.label}>
        <div className="workspace-nav-label">{group.label}</div>
        {group.items.map(([label, to, icon, end]) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `workspace-nav-link${isActive ? " is-active" : ""}`
            }
            onClick={() => {
              setMenuOpen(false);
              menuToggleRef.current?.focus();
            }}
          >
            <i className={`bi ${icon}`} aria-hidden="true" />
            <span>{label}</span>
          </NavLink>
        ))}
      </div>
    ));
  }

  return (
    <div className="app-shell workspace-shell">
      <a className="skip-link" href="#main-content">
        Saltar al contenido
      </a>
      <header className="workspace-topbar">
        <button
          className="workspace-menu-toggle"
          ref={menuToggleRef}
          type="button"
          aria-controls="workspace-navigation"
          aria-expanded={menuOpen}
          aria-label={menuOpen ? "Cerrar navegación" : "Abrir navegación"}
          onClick={() => setMenuOpen((open) => !open)}
        >
          <i className={`bi ${menuOpen ? "bi-x-lg" : "bi-list"}`} aria-hidden="true" />
        </button>
        <NavLink className="workspace-brand co-flex co-items-center" to="/" aria-label="SmileManager, inicio" onClick={() => setMenuOpen(false)}>
          <span className="workspace-brand-mark" aria-hidden="true">
            <i className="bi bi-heart-pulse-fill" />
          </span>
          <span>SmileManager</span>
        </NavLink>
        <div className="workspace-context workspace-clinic-context">
          {activeClinic ? <label className="workspace-clinic-selector">
            <i className="bi bi-building" aria-hidden="true" />
            <span className="workspace-clinic-selector-field">
              <span className="workspace-clinic-selector-label">Clínica actual</span>
              <select className="clinical-form-control workspace-clinic-select" aria-label="Clínica actual" value={activeClinic.id} disabled={clinicBusy} onChange={(event) => onClinicChange?.(event.target.value)}>
                {clinics.map((clinic) => <option key={clinic.id} value={clinic.id}>{clinic.name}</option>)}
              </select>
            </span>
            <i className={`bi ${clinicBusy ? "bi-hourglass-split" : "bi-chevron-down"} workspace-clinic-chevron`} aria-hidden="true" />
          </label> : "Operación clínica"}
        </div>
        <div className="workspace-user">
          <span className="workspace-user-avatar" aria-hidden="true">
            {(user?.username || "U").slice(0, 1).toUpperCase()}
          </span>
          <span className="workspace-user-name">{user?.username}</span>
          <button className="workspace-logout" type="button" onClick={handleLogout}>
            <i className="bi bi-box-arrow-right" aria-hidden="true" />
            <span>Salir</span>
          </button>
        </div>
      </header>

      {menuOpen && (
        <button
          type="button"
          className="workspace-scrim"
          aria-label="Cerrar navegación"
          onClick={() => {
            setMenuOpen(false);
            menuToggleRef.current?.focus();
          }}
        />
      )}
      {confirmLogout && <ConfirmDialog title="Salir con cambios sin guardar" confirmLabel="Salir sin guardar" busyLabel="Cerrando sesión…" busy={loggingOut} onClose={() => setConfirmLogout(false)} onConfirm={() => void finishLogout()}><p>Si cierras la sesión ahora, perderás los cambios que todavía no has guardado.</p></ConfirmDialog>}
      <div className="workspace-body">
        <aside
          id="workspace-navigation"
          className={`workspace-sidebar${menuOpen ? " is-open" : ""}`}
          ref={sidebarRef}
          role={menuOpen ? "dialog" : undefined}
          aria-modal={menuOpen ? "true" : undefined}
          aria-label="Navegación principal"
        >
          <nav>{renderNavigation()}</nav>
          <div className="workspace-sidebar-footer">
            <span className="workspace-clinic-mark" aria-hidden="true">SM</span>
            <span>SmileManager<br /><small>Gestión clínica</small></span>
          </div>
        </aside>
        <main id="main-content" className="workspace-main co-min-w-0" tabIndex={-1}>
          {patientMatch && (!activeClinic || activeClinic.role === "DOCTOR") && <PatientWorkspaceNav patientId={patientMatch[1]} />}
          {!activeClinic ? <section className="workspace-page"><h1>Bienvenido, {user?.username}</h1><p>No tienes clínicas activas asignadas. Solicita una invitación a la administración de tu clínica.</p>{user?.can_access_backoffice && <NavLink to="/backoffice">Abrir administración de plataforma</NavLink>}</section> : activeClinic.role === "CLINIC_ADMIN" ? <ClinicAdministrationPage key={activeClinic.id} aiEnabled={activeClinic.ai_effective} /> : activeClinic.role === "STAFF" ? <StaffAgendaPage key={activeClinic.id} /> : <Outlet key={`${activeClinic.id}:${location.pathname}`} context={{ activeClinic }} />}
          <footer className="workspace-footer">
            <span>SmileManager</span>
            <NavLink to="/privacy">Aviso de Privacidad</NavLink>
          </footer>
        </main>
      </div>
    </div>
  );
}
