import { useToast } from "../../context/ToastContext";
import { Link, useParams } from "react-router-dom";
import { useResource } from "../../hooks/useResource";
import type { Consultation } from "../../types/domain";
import { useState } from "react";
import { api, getErrorMessage } from "../../api/client";
import { useAuth } from "../../context/AuthContext";

export default function PrescriptionPage() {
  const toast = useToast();
  const { id } = useParams();
  const { data, error, reload } = useResource<Consultation>(
    `clinics/consultations/${id}/`,
  );
  const [updated, setUpdated] = useState<Consultation | null>(null);
  const item = updated || data;
  const { user } = useAuth();
  const [form, setForm] = useState({ password: "", code: "", text: "" });
  const [busy, setBusy] = useState(false);
  async function attest(operation: "close" | "addendum") {
    if (busy) return;
    setBusy(true);
    try {
      const result = await api<Consultation>(
        `clinics/consultations/${id}/${operation}/`,
        { method: "POST", body: JSON.stringify(form) },
      );
      setUpdated(result);
      toast.success(
        operation === "close" ? "Documento cerrado." : "Adenda registrada.",
      );
      setForm({ password: "", code: "", text: "" });
    } catch (reason) {
      toast.error(getErrorMessage(reason));
    } finally {
      setBusy(false);
    }
  }
  if (error)
    return (
      <div className="workspace-page co-mx-auto co-max-w-[1320px]">
        <div className="workspace-inline-error" role="alert">
          {error}
        </div>
        <button className="clinical-action-outline co-mt-3" onClick={reload}>
          Reintentar
        </button>
      </div>
    );
  if (!item)
    return (
      <div className="page-loader" role="status" aria-label="Cargando receta">
        <div className="workspace-loader-spinner" />
      </div>
    );
  return (
    <div className="workspace-page prescription-workspace co-mx-auto co-max-w-[1000px]">
      <div className="prescription-context">Consulta #{item.id}</div>
      <article className="prescription-sheet">
        <h1>Receta médica</h1>
        <p className="prescription-status">
          {item.status === "CLOSED"
            ? `Documento cerrado · ${item.author_name}`
            : item.status === "DRAFT"
              ? "Borrador pendiente de cierre"
              : "Documento histórico sin cierre acreditado"}
        </p>
        {item.integrity === "invalid" && (
          <p className="workspace-inline-error" role="alert">
            La integridad del documento requiere revisión. No utilizar como
            documento validado.
          </p>
        )}
        <div className="prescription-patient">
          <p>
            <strong>Paciente:</strong> {item.paciente.full_name}
          </p>
          <p>
            <strong>Fecha:</strong>{" "}
            {new Date(item.fecha_consulta).toLocaleString("es-MX")}
          </p>
        </div>
        <h2>Diagnóstico</h2>
        <p>{item.diagnostico}</p>
        <h2>Tratamiento</h2>
        <p>{item.tratamiento}</p>
        <h2>Observaciones</h2>
        <p>{item.observaciones}</p>
        {item.addenda?.map((row) => (
          <section className="prescription-addendum" key={row.id}>
            <h2>Adenda</h2>
            <p className="prescription-addendum-meta">
              {row.author_name} ·{" "}
              {new Date(row.created_at).toLocaleString("es-MX")} ·{" "}
              {row.integrity === "verified"
                ? "Integridad verificada"
                : "Requiere revisión"}
            </p>
            <p style={{ whiteSpace: "pre-wrap" }}>{row.text}</p>
          </section>
        ))}
      </article>
      {(item.status === "DRAFT" ||
        item.status === "LEGACY" ||
        (item.status === "CLOSED" && item.integrity === "verified")) && (
        <section
          className="workspace-section print-hidden"
          aria-labelledby="prescription-attestation-heading"
        >
          <div className="workspace-section-heading">
            <div>
              <h2 id="prescription-attestation-heading">
                {item.status === "DRAFT"
                  ? "Cerrar documento"
                  : "Agregar adenda"}
              </h2>
              <p>
                {item.status === "DRAFT"
                  ? "Confirma tu identidad para cerrar la receta."
                  : "Registra una corrección o aclaración del documento."}
              </p>
            </div>
          </div>
          <form
            className="prescription-attestation-body"
            onSubmit={(event) => {
              event.preventDefault();
              void attest(item.status === "DRAFT" ? "close" : "addendum");
            }}
          >
            {item.status !== "DRAFT" && (
              <div className="clinical-form-field">
                <label className="clinical-form-label" htmlFor="addendum-text">
                  Corrección o aclaración
                </label>
                <textarea
                  id="addendum-text"
                  className="clinical-form-control"
                  rows={4}
                  value={form.text}
                  minLength={10}
                  onChange={(event) =>
                    setForm({ ...form, text: event.target.value })
                  }
                />
                <span className="clinical-form-help">
                  Escribe al menos 10 caracteres.
                </span>
              </div>
            )}
            <div className="clinical-form-field">
              <label
                className="clinical-form-label"
                htmlFor="document-password"
              >
                Confirma tu contraseña
              </label>
              <input
                id="document-password"
                className="clinical-form-control"
                type="password"
                autoComplete="current-password"
                value={form.password}
                onChange={(event) =>
                  setForm({ ...form, password: event.target.value })
                }
              />
            </div>
            {user?.mfa_enabled && (
              <div className="clinical-form-field">
                <label className="clinical-form-label" htmlFor="document-code">
                  Código del autenticador
                </label>
                <input
                  id="document-code"
                  className="clinical-form-control"
                  autoComplete="one-time-code"
                  value={form.code}
                  onChange={(event) =>
                    setForm({ ...form, code: event.target.value })
                  }
                />
              </div>
            )}
            <div className="prescription-attestation-actions">
              <Link className="clinical-action-outline" to="/security">
                <i className="bi bi-shield-check" aria-hidden="true" />
                Revisar mi nombre y seguridad
              </Link>
              <button
                type="submit"
                className="clinical-action-primary"
                disabled={
                  busy ||
                  !form.password ||
                  (item.status !== "DRAFT" && form.text.trim().length < 10)
                }
              >
                {busy ? (
                  <>
                    <span
                      className="clinical-form-spinner"
                      aria-hidden="true"
                    />
                    Guardando…
                  </>
                ) : item.status === "DRAFT" ? (
                  "Confirmar cierre"
                ) : (
                  "Guardar adenda"
                )}
              </button>
            </div>
          </form>
          <p className="workspace-section-note">
            El cierre vincula el contenido con tu identidad autenticada y evita
            su modificación ordinaria. No equivale a firma electrónica avanzada.
            Una adenda histórica no acredita la firma del documento original.
          </p>
        </section>
      )}
      <div className="prescription-page-actions print-hidden">
        <div className="co-flex co-flex-wrap co-gap-3">
          <Link
            className="clinical-action-outline"
            to={`/patients/${item.paciente.id}`}
          >
            Ver paciente
          </Link>
          <Link
            className="clinical-action-outline"
            to={`/patients/${item.paciente.id}/consultations`}
          >
            Historial de consultas
          </Link>
        </div>
        <button
          className="clinical-action-primary"
          type="button"
          disabled={item.status === "DRAFT" || item.integrity === "invalid"}
          onClick={() => window.print()}
        >
          <i className="bi bi-printer" aria-hidden="true" />
          Descargar PDF / Imprimir
        </button>
      </div>
    </div>
  );
}
