import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { useParams } from "react-router-dom";
import { getErrorMessage, getFormErrors } from "../../api/client";
import { useToast } from "../../context/ToastContext";
import type { Consent } from "../../types/domain";
import { clinicalService } from "../../services/clinical";
import { useUnsavedChanges } from "../../hooks/useUnsavedChanges";
import { useApiDownload } from "../../hooks/useApiDownload";

const clauses = [
  "He sido informado(a) de manera clara, completa y comprendo la necesidad de ser atendido(a) por el especialista.",
  "He sido informado(a) de las alternativas posibles de tratamiento que requiero.",
  "Acepto cualquier prueba diagnóstica necesaria, incluidos estudios radiológicos.",
  "Comprendo la necesidad de utilizar anestesia local para el tratamiento indicado.",
  "Comprendo los posibles riesgos, molestias, efectos secundarios y complicaciones.",
  "Comprendo que la medicina no es una ciencia exacta y no existen garantías sobre el resultado.",
  "Me han sido explicados los cuidados postoperatorios necesarios.",
];
export default function ConsentPage() {
  const toast = useToast();
  const { id } = useParams();
  const [consent, setConsent] = useState<Consent | null>(null);
  const [accepted, setAccepted] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const guard = useUnsavedChanges(accepted || file !== null);
  const [error, setError] = useState("");
  const [loadError, setLoadError] = useState("");
  const [saving, setSaving] = useState(false);
  const { active: downloadActive, download } = useApiDownload();
  const [reload, setReload] = useState(0);
  useEffect(() => {
    clinicalService.consent(id!).then((result) => {
      setConsent(result);
      setLoadError("");
    }).catch((requestError) => setLoadError(requestError.message));
  }, [id, reload]);
  if (loadError && !consent)
    return <div className="workspace-page co-mx-auto co-max-w-[1320px]"><div className="workspace-inline-error" role="alert">{loadError}</div><button className="clinical-action-outline co-mt-3" onClick={() => setReload((value) => value + 1)}>Reintentar</button></div>;
  if (!consent)
    return (
      <div className="page-loader" role="status" aria-label="Cargando consentimiento">
        <div className="workspace-loader-spinner" />
      </div>
    );
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (saving) return;
    setSaving(true);
    setError("");
    const data = new FormData();
    data.append("texto", clauses.join("\n"));
    if (file) data.append("archivo_ine", file);
    try {
      setConsent(
        await clinicalService.saveConsent(id!, data),
      );
      setAccepted(false);
      setFile(null);
      toast.success("Consentimiento guardado correctamente.");
    } catch (err) {
      const fieldError = getFormErrors<"archivo_ine">(err).archivo_ine;
      const message = Array.isArray(fieldError) ? fieldError.join(" ") : fieldError || getErrorMessage(err);
      setError(message);
      toast.error(message);
    } finally {
      setSaving(false);
    }
  }
  return (
    <div className="workspace-page co-mx-auto co-max-w-[1320px]">
      <div className="clinical-form-surface co-mx-auto consent-card">
        <div className="clinical-consent-content">
          <h1>Consentimiento Informado</h1>
          <p className="clinical-consent-description">
            Documento de autorización para tratamiento odontológico
          </p>
          <p className="clinical-consent-lead">
            Declaro en pleno uso de mis facultades mentales, libre y
            responsablemente:
          </p>
          <ul>
            {clauses.map((clause) => (
              <li key={clause}>
                {clause}
              </li>
            ))}
          </ul>
          {consent.fecha_aceptacion ? (
            <div className="workspace-inline-success" role="status" aria-live="polite">
              <h2 className="clinical-consent-accepted-title">Consentimiento aceptado</h2>
              <p>{new Date(consent.fecha_aceptacion).toLocaleString("es-MX")}</p>
              {consent.archivo_ine_url && (
                <a
                  href={consent.archivo_ine_url}
                  target="_blank"
                  rel="noreferrer"
                  aria-disabled={Boolean(downloadActive)}
                  onClick={(event) => {
                    event.preventDefault();
                    void download("identification", `patients/${id}/consent/file/`, `Identificacion_${id}`);
                  }}
                  className="clinical-action-outline clinical-action-compact"
                >
                  {downloadActive ? "Preparando descarga…" : "Descargar identificación"}
                </a>
              )}
            </div>
          ) : (
            <form onSubmit={submit}>
              <p className="clinical-form-help">Esta acción guarda la aceptación y la identificación en el expediente mostrado. Verifica el paciente antes de continuar.</p>
              <div className="clinical-consent-accept">
                <input
                  id="accept-consent"
                  type="checkbox"
                  className="clinical-checkbox"
                  checked={accepted}
                  required
                  onChange={(e) => {
                    setAccepted(e.target.checked);
                    setError("");
                  }}
                />
                <label
                  htmlFor="accept-consent"
                  className="clinical-consent-accept-label"
                >
                  He leído y acepto los términos.
                </label>
              </div>
              <label htmlFor="ine" className="clinical-form-label">
                Identificación oficial
              </label>
              <input
                id="ine"
                type="file"
                required
                disabled={!accepted}
                accept="image/*,application/pdf"
                className="clinical-form-control"
                aria-invalid={Boolean(error)}
                aria-describedby={error ? "ine-help ine-error" : "ine-help"}
                onChange={(e) => {
                  setFile(e.target.files?.[0] ?? null);
                  setError("");
                }}
              />
              <small id="ine-help" className="clinical-form-help">
                JPG, PNG, GIF o PDF; máximo 5 MB.
              </small>
              {error && <div id="ine-error" className="clinical-form-field-error">{error}</div>}
              <div className="clinical-form-actions"><button
                disabled={!accepted || !file || saving}
                className="clinical-form-submit"
              >
                {saving ? "Guardando…" : "Aceptar y guardar"}
              </button></div>
            </form>
          )}
        </div>
      </div>
    {guard.prompt}</div>
  );
}
