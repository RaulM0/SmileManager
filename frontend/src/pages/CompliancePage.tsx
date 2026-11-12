import { useToast } from "../context/ToastContext";
import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  api,
  ApiError,
  getClinicContext,
  getErrorMessage,
  getFormErrors,
} from "../api/client";
import FieldLabelHelp from "../components/FieldLabelHelp";
import { noticeGuidance, templateGuidance } from "../utils/complianceGuidance";
import { noticeFields } from "../types/compliance";
import type { ConsentTemplate, Notice } from "../types/compliance";

export default function CompliancePage() {
  const toast = useToast();
  const [body, setBody] = useState<Record<string, string>>(
    Object.fromEntries(noticeFields.map(([key]) => [key, ""])),
  );
  const [notice, setNotice] = useState<Notice | null>(null);
  const [templates, setTemplates] = useState<ConsentTemplate[]>([]);
  const [reviewed, setReviewed] = useState(false);
  const [templateReviewed, setTemplateReviewed] = useState(false);
  const [template, setTemplate] = useState({
    kind: "CLINICAL",
    title: "",
    text: "",
  });
  const [profileRequired, setProfileRequired] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [reload, setReload] = useState(0);
  const [loaded, setLoaded] = useState(false);
  const [loadError, setLoadError] = useState("");
  const bodyEdited = useRef(false);
  useEffect(() => {
    if (!getClinicContext()) return;
    let live = true;
    Promise.all([
      api<{ notice: Notice | null }>("clinics/privacy/"),
      api<ConsentTemplate[]>("clinics/admin/consent-templates/"),
    ])
      .then(([result, rows]) => {
        if (!live) return;
        setNotice(result.notice);
        if (result.notice && !bodyEdited.current) setBody(result.notice.body);
        setTemplates(rows);
        setLoaded(true);
      })
      .catch((reason) => {
        if (live) setLoadError(getErrorMessage(reason));
      });
    return () => {
      live = false;
    };
  }, [reload]);
  function showPublishError(reason: unknown) {
    const errors = getFormErrors<string>(reason);
    const text = (value: unknown) =>
      Array.isArray(value)
        ? value.join(" ")
        : typeof value === "string"
          ? value
          : "";
    const fields = Object.fromEntries(
      Object.entries(errors)
        .filter(([key]) => !["detail", "code"].includes(key))
        .map(([key, value]) => [key, text(value)]),
    );
    setFieldErrors(fields);
    setProfileRequired(
      reason instanceof ApiError &&
        reason.payload?.code === "profile_name_required",
    );
    toast.error(
      text(errors.detail) ||
        (Object.keys(fields).length
          ? "Revisa los campos señalados antes de publicar."
          : getErrorMessage(reason)),
    );
  }
  const header = (
    <header className="workspace-page-header">
      <div>
        <h1>Privacidad y consentimientos</h1>
        <p className="clinical-page-description">
          Administra el aviso de privacidad y las plantillas de tu clínica.
        </p>
      </div>
      <Link className="clinical-action-outline" to="/">
        <i className="bi bi-arrow-left" aria-hidden="true" />
        Volver al espacio de trabajo
      </Link>
    </header>
  );
  if (!getClinicContext())
    return (
      <main className="workspace-page compliance-workspace co-mx-auto co-max-w-[1100px]">
        {header}
        <div className="workspace-section">
          <div className="workspace-empty-state">
            Selecciona una clínica en el espacio de trabajo para continuar.
          </div>
        </div>
      </main>
    );
  if (loadError || !loaded)
    return (
      <main className="workspace-page compliance-workspace co-mx-auto co-max-w-[1100px]">
        {header}
        <p
          className={
            loadError ? "workspace-inline-error" : "clinical-page-description"
          }
          role={loadError ? "alert" : "status"}
        >
          {loadError || "Cargando configuración de la clínica…"}
        </p>
      </main>
    );
  return (
    <main className="workspace-page compliance-workspace co-mx-auto co-max-w-[1100px]">
      {header}
      <div className="compliance-notice">
        <i className="bi bi-info-circle" aria-hidden="true" />
        <p>
          Solo la administración de la clínica puede publicar. Cada publicación
          conserva una versión independiente; confirma la revisión jurídica y
          clínica antes de continuar.
        </p>
      </div>
      {profileRequired && (
        <div className="compliance-notice">
          <i className="bi bi-person" aria-hidden="true" />
          <div>
            <Link to="/security" target="_blank" rel="noopener noreferrer">
              Completar mi nombre en Seguridad de mi cuenta (abre otra pestaña)
            </Link>
            <span className="clinical-form-help">
              Guarda tu nombre y apellidos allí y vuelve a publicar aquí. El
              contenido de este formulario se conserva mientras mantengas esta
              pestaña abierta.
            </span>
          </div>
        </div>
      )}

      <form
        className="workspace-section"
        onSubmit={async (event) => {
          event.preventDefault();
          if (busy) return;
          setBusy(true);
          setProfileRequired(false);
          setFieldErrors({});
          try {
            const result = await api<Notice>("clinics/admin/privacy/", {
              method: "POST",
              body: JSON.stringify({ ...body, review_confirmed: reviewed }),
            });
            toast.success(`Aviso versión ${result.version} publicado.`);
            setReviewed(false);
            bodyEdited.current = false;
            setLoaded(false);
            setReload((value) => value + 1);
          } catch (reason) {
            showPublishError(reason);
          } finally {
            setBusy(false);
          }
        }}
      >
        <div className="workspace-section-heading">
          <div>
            <h2>Aviso de privacidad</h2>
            <p>
              {notice
                ? `Versión actual ${notice.version}`
                : "Pendiente de configuración"}
            </p>
          </div>
          <i
            className="bi bi-shield-check compliance-section-icon"
            aria-hidden="true"
          />
        </div>
        <div className="compliance-form-body">
          {noticeFields.map(([key, label]) => (
            <div className="clinical-form-field" key={key}>
              <FieldLabelHelp
                htmlFor={`notice-${key}`}
                label={label}
                guidance={noticeGuidance[key]}
              />
              {key === "privacy_email" ? (
                <input
                  id={`notice-${key}`}
                  aria-invalid={Boolean(fieldErrors[key])}
                  aria-describedby={`notice-${key}-help${fieldErrors[key] ? ` notice-${key}-error` : ""}`}
                  type="email"
                  maxLength={254}
                  className="clinical-form-control"
                  required
                  value={body[key]}
                  onChange={(event) => {
                    bodyEdited.current = true;
                    setBody({ ...body, [key]: event.target.value });
                  }}
                />
              ) : (
                <textarea
                  id={`notice-${key}`}
                  aria-invalid={Boolean(fieldErrors[key])}
                  aria-describedby={`notice-${key}-help${fieldErrors[key] ? ` notice-${key}-error` : ""}`}
                  className="clinical-form-control"
                  rows={3}
                  required
                  maxLength={
                    key === "legal_name"
                      ? 300
                      : key === "address"
                        ? 1000
                        : key === "arco_procedure"
                          ? 20000
                          : 10000
                  }
                  value={body[key]}
                  onChange={(event) => {
                    bodyEdited.current = true;
                    setBody({ ...body, [key]: event.target.value });
                  }}
                />
              )}
              {fieldErrors[key] && (
                <span
                  id={`notice-${key}-error`}
                  className="clinical-form-field-error"
                >
                  {fieldErrors[key]}
                </span>
              )}
            </div>
          ))}
          {fieldErrors.review_confirmed && (
            <p className="clinical-form-field-error">
              {fieldErrors.review_confirmed}
            </p>
          )}
          <label className="consent-attestation">
            <input
              type="checkbox"
              checked={reviewed}
              required
              onChange={(event) => setReviewed(event.target.checked)}
            />{" "}
            El responsable revisó estos datos y los procedimientos están
            disponibles para los titulares.
          </label>
          <div className="compliance-form-actions">
            <button
              className="clinical-action-primary"
              disabled={busy || !reviewed}
            >
              <i className="bi bi-check2" aria-hidden="true" />
              Publicar nueva versión del aviso
            </button>
          </div>
        </div>
      </form>
      <form
        className="workspace-section"
        onSubmit={async (event) => {
          event.preventDefault();
          if (busy) return;
          setBusy(true);
          setProfileRequired(false);
          setFieldErrors({});
          try {
            await api("clinics/admin/consent-templates/", {
              method: "POST",
              body: JSON.stringify({
                ...template,
                review_confirmed: templateReviewed,
              }),
            });
            toast.success("Nueva versión de plantilla publicada.");
            setTemplateReviewed(false);
            setLoaded(false);
            setReload((value) => value + 1);
          } catch (reason) {
            showPublishError(reason);
          } finally {
            setBusy(false);
          }
        }}
      >
        <div className="workspace-section-heading">
          <div>
            <h2>Plantilla de consentimiento</h2>
            <p>Publica el contenido aprobado para la firma del paciente.</p>
          </div>
          <i
            className="bi bi-file-earmark-text compliance-section-icon"
            aria-hidden="true"
          />
        </div>
        <div className="compliance-form-body">
          <p className="compliance-form-description">
            El texto debe corresponder al documento que firmará el paciente o
            representante. La carga posterior registra evidencia documental; no
            autentica por sí misma al firmante.
          </p>
          <FieldLabelHelp
            htmlFor="template-kind"
            label="Tipo"
            guidance={templateGuidance.kind}
          />
          <select
            id="template-kind"
            aria-invalid={Boolean(fieldErrors["kind"])}
            aria-describedby={`template-kind-help${fieldErrors["kind"] ? " template-kind-error" : ""}`}
            className="clinical-form-control"
            value={template.kind}
            onChange={(event) =>
              setTemplate({ ...template, kind: event.target.value })
            }
          >
            <option value="CLINICAL">Clínico</option>
            <option value="PRIVACY">Tratamiento de datos personales</option>
          </select>
          {fieldErrors.kind && (
            <span
              id="template-kind-error"
              className="clinical-form-field-error"
            >
              {fieldErrors.kind}
            </span>
          )}
          <FieldLabelHelp
            htmlFor="template-title"
            label="Título"
            guidance={templateGuidance.title}
          />
          <input
            id="template-title"
            aria-invalid={Boolean(fieldErrors["title"])}
            aria-describedby={`template-title-help${fieldErrors["title"] ? " template-title-error" : ""}`}
            className="clinical-form-control"
            required
            maxLength={250}
            value={template.title}
            onChange={(event) =>
              setTemplate({ ...template, title: event.target.value })
            }
          />
          {fieldErrors.title && (
            <span
              id="template-title-error"
              className="clinical-form-field-error"
            >
              {fieldErrors.title}
            </span>
          )}
          <FieldLabelHelp
            htmlFor="template-text"
            label="Texto completo aprobado"
            guidance={templateGuidance.text}
          />
          <textarea
            id="template-text"
            aria-invalid={Boolean(fieldErrors["text"])}
            aria-describedby={`template-text-help${fieldErrors["text"] ? " template-text-error" : ""}`}
            className="clinical-form-control"
            rows={12}
            required
            minLength={20}
            maxLength={100000}
            value={template.text}
            onChange={(event) =>
              setTemplate({ ...template, text: event.target.value })
            }
          />
          {fieldErrors.text && (
            <span
              id="template-text-error"
              className="clinical-form-field-error"
            >
              {fieldErrors.text}
            </span>
          )}
          <label className="consent-attestation">
            <input
              type="checkbox"
              checked={templateReviewed}
              required
              onChange={(event) => setTemplateReviewed(event.target.checked)}
            />{" "}
            Se revisaron el contenido, la representación y el procedimiento de
            documento firmado adjunto.
          </label>
          <div className="compliance-form-actions">
            <button
              className="clinical-action-primary"
              disabled={busy || !templateReviewed || !notice}
            >
              <i className="bi bi-check2" aria-hidden="true" />
              Publicar nueva versión de plantilla
            </button>
          </div>
          {!notice && (
            <p className="clinical-form-help">
              Publica primero el aviso de privacidad para habilitar las
              plantillas.
            </p>
          )}
        </div>
      </form>
      <section
        className="workspace-section"
        aria-labelledby="published-templates-heading"
      >
        <div className="workspace-section-heading">
          <div>
            <h2 id="published-templates-heading">Versiones publicadas</h2>
            <p>Plantillas de consentimiento disponibles en la clínica</p>
          </div>
        </div>
        {templates.length ? (
          <ul className="compliance-template-list">
            {templates.map((row) => (
              <li key={row.id}>
                <div>
                  <strong>{row.title}</strong>
                  <span>
                    {row.kind === "CLINICAL" ? "Clínico" : "Datos personales"}
                  </span>
                </div>
                <span className="compliance-version">
                  Versión {row.version}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <div className="workspace-empty-state">
            <i className="bi bi-file-earmark-text" aria-hidden="true" />
            <span>No hay plantillas publicadas.</span>
          </div>
        )}
      </section>
    </main>
  );
}
