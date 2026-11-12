import { useLayoutEffect, useRef } from "react";
import { NavLink, useLocation } from "react-router-dom";
import type { Patient } from "../../types/domain";
import { useResource } from "../../hooks/useResource";

const sections: Array<[string, string, boolean?]> = [
  ["Resumen", "", true],
  ["Expediente", "/record"],
  ["Antecedentes", "/medical-history"],
  ["Consultas", "/consultations"],
  ["Odontograma", "/odontogram"],
  ["Imágenes", "/images"],
  ["Progreso", "/comparative-study"],
  ["Consentimiento", "/consent"],
];

export default function PatientWorkspaceNav({
  patientId,
}: {
  patientId: string;
}) {
  const { data: patient } = useResource<Patient>(
    `clinics/patients/${patientId}/`,
  );
  const { pathname } = useLocation();
  const linksRef = useRef<HTMLDivElement>(null);
  const navRef = useRef<HTMLElement>(null);
  useLayoutEffect(() => {
    const links = linksRef.current;
    const nav = navRef.current;
    if (!links || !nav) return;
    const updateIndicator = () => {
      nav.dataset.more = String(
        links.scrollWidth - links.clientWidth - links.scrollLeft > 2,
      );
    };
    if (window.matchMedia("(max-width: 991.98px)").matches) {
      const active = links.querySelector<HTMLElement>('a[aria-current="page"]');
      if (active)
        links.scrollLeft =
          active.offsetLeft -
          links.offsetLeft -
          (links.clientWidth - active.offsetWidth) / 2;
    }
    updateIndicator();
    links.addEventListener("scroll", updateIndicator, { passive: true });
    window.addEventListener("resize", updateIndicator);
    const observer =
      typeof ResizeObserver === "undefined"
        ? null
        : new ResizeObserver(updateIndicator);
    observer?.observe(links);
    return () => {
      links.removeEventListener("scroll", updateIndicator);
      window.removeEventListener("resize", updateIndicator);
      observer?.disconnect();
    };
  }, [pathname, patientId]);
  const patientName = patient
    ? [patient.nombre, patient.appat, patient.apmat].filter(Boolean).join(" ")
    : "";
  return (
    <nav
      ref={navRef}
      className="patient-workspace-nav"
      aria-label="Secciones del expediente"
    >
      <div className="patient-workspace-context">
        <i className="bi bi-person-vcard" aria-hidden="true" />
        <span
          className="patient-workspace-identity"
          title={patientName || undefined}
        >
          Expediente <strong>#{patientId}</strong>
          {patientName && (
            <span className="patient-workspace-name"> · {patientName}</span>
          )}
        </span>
      </div>
      <div ref={linksRef} className="patient-workspace-links">
        {sections.map(([label, suffix, end]) => {
          const to = `/patients/${patientId}${suffix}`;
          return (
            <NavLink
              key={label}
              to={to}
              end={Boolean(end)}
              className={({ isActive }) => (isActive ? "is-active" : undefined)}
            >
              {label}
            </NavLink>
          );
        })}
      </div>
    </nav>
  );
}
