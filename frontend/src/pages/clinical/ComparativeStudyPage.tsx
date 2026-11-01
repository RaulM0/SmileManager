import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { useParams } from "react-router-dom";
import { getErrorMessage, getFormErrors } from "../../api/client";
import type { ComparativeStudy, FieldErrors } from "../../types/domain";
import { useToast } from "../../context/ToastContext";
import { useProtectedMedia } from "../../hooks/useProtectedMedia";
import { clinicalService } from "../../services/clinical";
import { useUnsavedChanges } from "../../hooks/useUnsavedChanges";
import { useApiDownload } from "../../hooks/useApiDownload";
import { useQueryClient } from "@tanstack/react-query";

function formSnapshot(form: HTMLFormElement) {
  return JSON.stringify(Array.from(new FormData(form), ([name, value]) => [name, typeof value === "string" ? value : value.name ? [value.name, value.size, value.lastModified] : null]));
}

const before = [
  ["antes_oclusal_superior", "Oclusal superior"],
  ["antes_lateral_izquierda", "Lateral izquierda"],
  ["antes_frontal", "Frontal"],
  ["antes_lateral_derecha", "Lateral derecha"],
  ["antes_oclusal_inferior", "Oclusal inferior"],
];
const after = [
  ["despues_perfil", "Perfil"],
  ["despues_semiperfil", "Semiperfil"],
  ["despues_retrato_frontal", "Retrato frontal"],
  ["despues_retrato_sonrisa", "Retrato sonrisa"],
];
function ImageField({ name, label, required = false, url, error, onFile, mediaPath }: {
  name: string;
  label: string;
  required?: boolean;
  url?: string | null;
  error?: string | null;
  onFile: (name: string, file: File | null) => void;
  mediaPath?: string;
}) {
  const preview = useProtectedMedia(url && mediaPath ? mediaPath : null);
  return (
    <div className="clinical-study-field">
          <label htmlFor={name} className="clinical-form-label">
            {label}
          </label>
          {url && (preview ? <img src={preview} alt={label} className="study-preview" /> : <div className="study-preview" role="status" aria-label={`Cargando ${label}`} />)}
          <input
            id={name}
            type="file"
            accept="image/*"
            required={required && !url}
            className="clinical-form-control"
            aria-invalid={Boolean(error)}
            aria-describedby={error ? `${name}-error` : undefined}
            onChange={(e) => onFile(name, e.target.files?.[0] ?? null)}
          />
          {error && <div id={`${name}-error`} className="clinical-form-field-error">{error}</div>}
    </div>
  );
}
export default function ComparativeStudyPage() {
  const toast = useToast();
  const queryClient = useQueryClient();
  const { id } = useParams();
  const [study, setStudy] = useState<ComparativeStudy | null>(null);
  const [files, setFiles] = useState<Record<string, File | null>>({});
  const baseline = useRef<string | null>(null);
  const [dirty, setDirty] = useState(false);
  const guard = useUnsavedChanges(dirty);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [loadError, setLoadError] = useState("");
  const [saving, setSaving] = useState(false);
  const { active: downloadActive, download } = useApiDownload();
  const [reload, setReload] = useState(0);
  const errorText = (name: string) => {
    const message = errors[name];
    if (!message) return null;
    return Array.isArray(message) ? message.join(" ") : message;
  };
  const clearFieldError = (name: string) =>
    setErrors((current) => ({ ...current, [name]: undefined, detail: undefined }));
  const updateFile = (name: string, file: File | null) => {
    setFiles((current) => ({ ...current, [name]: file }));
    clearFieldError(name);
  };
  useEffect(() => {
    clinicalService.comparativeStudy(id!).then((result) => {
      setStudy(result);
      setLoadError("");
    }).catch((requestError) => setLoadError(requestError.message));
  }, [id, reload]);
  if (loadError && !study)
    return <div className="workspace-page co-mx-auto co-max-w-[1320px]"><div className="workspace-inline-error" role="alert">{loadError}</div><button className="clinical-action-outline co-mt-3" onClick={() => setReload((value) => value + 1)}>Reintentar</button></div>;
  if (!study)
    return (
      <div className="page-loader" role="status" aria-label="Cargando estudio comparativo">
        <div className="workspace-loader-spinner" />
      </div>
    );
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (saving) return;
    setSaving(true);
    setErrors({});
    const data = new FormData(e.currentTarget);
    const formElement = e.currentTarget;
    const submittedSnapshot = formSnapshot(formElement);
    Object.entries(files).forEach(
      ([name, file]) => file && data.set(name, file),
    );
    try {
      setStudy(
        await clinicalService.saveComparativeStudy(id!, data),
      );
      await queryClient.invalidateQueries({
        predicate: (query) => query.queryKey[0] === "protected-media" && typeof query.queryKey[1] === "string" && query.queryKey[1].startsWith(`patients/${id}/comparative-study/`),
      });
      setFiles({});
      baseline.current = submittedSnapshot;
      const stillDirty = formSnapshot(formElement) !== submittedSnapshot;
      setDirty(stillDirty);
      toast.success("Estudio guardado correctamente.");
    } catch (error) {
      setErrors(getFormErrors(error));
      toast.error(getErrorMessage(error));
    } finally {
      setSaving(false);
    }
  }
  return (
    <div className="workspace-page co-mx-auto co-max-w-[1320px]">
      <div className="workspace-page-header">
        <div><h1>Estudio comparativo</h1></div>
        {study.exists && (
          <a
            className="clinical-action-outline"
            href={`/api/v1/patients/${id}/comparative-study/pdf/`}
            aria-disabled={Boolean(downloadActive)}
            onClick={(event) => {
              event.preventDefault();
              void download("study", `patients/${id}/comparative-study/pdf/`, `Estudio_${id}.pdf`);
            }}
          >
            <i className="bi bi-file-pdf" aria-hidden="true" />
            {downloadActive ? "Preparando descarga…" : "Descargar PDF"}
          </a>
        )}
      </div>
      {loadError && <div className="workspace-inline-warning co-mb-4" role="alert">{loadError}</div>}
      <form onSubmit={submit} ref={(node) => { if (node && baseline.current === null) baseline.current = formSnapshot(node); }} onChange={(event) => setDirty(formSnapshot(event.currentTarget) !== baseline.current)}>
        <div className="clinical-form-surface co-mb-5">
          <div className="clinical-form-body">
            <div className="clinical-form-grid">
              <div className="clinical-form-col-4">
                <label htmlFor="fecha_inicio" className="clinical-form-label">
                  Fecha de inicio
                </label>
                <input
                  id="fecha_inicio"
                  name="fecha_inicio"
                  type="date"
                  required
                  className="clinical-form-control"
                  aria-invalid={Boolean(errors.fecha_inicio)}
                  aria-describedby={errors.fecha_inicio ? "fecha_inicio-error" : undefined}
                  defaultValue={study.fecha_inicio || ""}
                  onChange={() => clearFieldError("fecha_inicio")}
                />
                {errors.fecha_inicio && <div id="fecha_inicio-error" className="clinical-form-field-error">{errorText("fecha_inicio")}</div>}
              </div>
              <div className="clinical-form-col-8">
                <label htmlFor="diagnostico" className="clinical-form-label">
                  Diagnóstico
                </label>
                <input
                  id="diagnostico"
                  name="diagnostico"
                  className="clinical-form-control"
                  aria-invalid={Boolean(errors.diagnostico)}
                  aria-describedby={errors.diagnostico ? "diagnostico-error" : undefined}
                  defaultValue={study.diagnostico || ""}
                  onChange={() => clearFieldError("diagnostico")}
                />
                {errors.diagnostico && <div id="diagnostico-error" className="clinical-form-field-error">{errorText("diagnostico")}</div>}
              </div>
              <div className="clinical-form-col-full">
                <label htmlFor="observaciones" className="clinical-form-label">
                  Observaciones
                </label>
                <textarea
                  id="observaciones"
                  name="observaciones"
                  className="clinical-form-control"
                  aria-invalid={Boolean(errors.observaciones)}
                  aria-describedby={errors.observaciones ? "observaciones-error" : undefined}
                  defaultValue={study.observaciones || ""}
                  onChange={() => clearFieldError("observaciones")}
                />
                {errors.observaciones && <div id="observaciones-error" className="clinical-form-field-error">{errorText("observaciones")}</div>}
              </div>
            </div>
          </div>
        </div>
        <h2 className="clinical-study-heading">Imágenes antes</h2>
        {!study.exists && <p className="clinical-form-help">Las cinco imágenes iniciales son obligatorias para registrar el estudio.</p>}
        <div className="clinical-study-grid co-mb-5">
          {before.map(([name, label]) => (
            <ImageField
              key={name}
              name={name}
              label={label}
              required={!study.exists}
              url={study.image_urls?.[name]}
              mediaPath={`patients/${id}/comparative-study/media/${name}/`}
              error={errorText(name)}
              onFile={updateFile}
            />
          ))}
        </div>
        <h2 className="clinical-study-heading">Imágenes después</h2>
        <div className="clinical-study-grid co-mb-5">
          {after.map(([name, label]) => (
            <ImageField
              key={name}
              name={name}
              label={label}
              url={study.image_urls?.[name]}
              mediaPath={`patients/${id}/comparative-study/media/${name}/`}
              error={errorText(name)}
              onFile={updateFile}
            />
          ))}
        </div>
        <div className="clinical-form-actions"><button className="clinical-form-submit" disabled={saving}>{saving ? "Guardando…" : "Guardar estudio"}</button></div>
      </form>{guard.prompt}
    </div>
  );
}
