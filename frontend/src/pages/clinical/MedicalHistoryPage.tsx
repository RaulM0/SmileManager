import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { useParams } from "react-router-dom";
import { getErrorMessage, getFormErrors } from "../../api/client";
import { useToast } from "../../context/ToastContext";
import type { FieldErrors, MedicalHistory, Patient } from "../../types/domain";
import { patientsService } from "../../services/patients";
import { clinicalService } from "../../services/clinical";
import { useUnsavedChanges } from "../../hooks/useUnsavedChanges";

const questions = [
  ["tratamiento_medico", "¿Está en tratamiento médico?"],
  ["problemas_cardiacos", "¿Tiene problemas cardíacos?"],
  ["problemas_coagulacion", "¿Tiene problemas de coagulación?"],
  ["epilepsia", "Epilepsia/Convulsiones"],
  ["gastritis", "Gastritis/Úlceras"],
  ["hipertension", "Hipertensión"],
  ["anemia", "Anemia"],
  ["embarazo", "Embarazo/Sospecha de embarazo"],
  ["alergia_medicamentos", "Alergia a algún medicamento"],
  ["alergia_especifica", "Alergia específica"],
  ["discapacidad", "Discapacidad"],
  ["fuma", "¿Fuma?"],
  ["respiracion_bucal", "Respiración bucal"],
  ["morder_unas", "Morderse las uñas"],
  ["chupar_dedo", "Chupar dedo o labios"],
  ["rechinar_dientes", "Rechinar los dientes"],
  ["sobremordida_vertical", "Sobremordida vertical"],
  ["sobremordida_horizontal", "Sobremordida horizontal"],
  ["mordida_cruzada", "Mordida cruzada"],
  ["mordida_abierta", "Mordida abierta"],
  ["desgaste", "Desgaste - Abrasión"],
  ["problemas_atm", "Problemas ATM chasquidos"],
  ["consumo_citricos", "Consumo frecuente de cítricos"],
  ["sangrado_encias", "Sangrado de encías"],
];
const texts = [
  ["alergias", "Alergias"],
  ["medicamentos", "Medicamentos"],
  ["cirugias_previas", "Cirugías previas"],
  ["otros", "Otros"],
];
const questionGroups = [
  { title: "Salud general", items: questions.slice(0, 12) },
  { title: "Salud oral y hábitos", items: questions.slice(12) },
];
export default function MedicalHistoryPage() {
  const toast = useToast();
  const { id } = useParams();
  const [history, setHistory] = useState<MedicalHistory | null>(null);
  const [baseline, setBaseline] = useState<string | null>(null);
  const guard = useUnsavedChanges(history !== null && baseline !== null && JSON.stringify(history) !== baseline);
  const [patient, setPatient] = useState<Patient | null>(null);
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [saving, setSaving] = useState(false);
  const [reload, setReload] = useState(0);
  useEffect(() => {
    Promise.all([
      patientsService.get(id!),
      clinicalService.medicalHistory(id!),
    ]).then(([p, h]) => {
      setPatient(p);
      setHistory(h);
      setBaseline(JSON.stringify(h));
      setError("");
    }).catch((requestError) => setError(requestError.message));
  }, [id, reload]);
  if (!history || !patient)
    return error ? (
      <div className="workspace-page co-mx-auto co-max-w-[1560px]">
        <div className="workspace-inline-error" role="alert">{error}</div>
        <button className="clinical-action-outline co-mt-3" onClick={() => setReload((value) => value + 1)}>Reintentar</button>
      </div>
    ) : (
      <div className="page-loader" role="status" aria-label="Cargando antecedentes">
        <div className="workspace-loader-spinner" />
      </div>
    );
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (saving) return;
    setSaving(true);
    setError("");
    setFieldErrors({});
    try {
      const saved = await clinicalService.saveMedicalHistory(id!, history!);
      setHistory(saved);
      setBaseline(JSON.stringify(saved));
      toast.success("Antecedentes actualizados.");
    } catch (requestError) {
      setFieldErrors(getFormErrors(requestError));
      toast.error(getErrorMessage(requestError));
    } finally {
      setSaving(false);
    }
  }
  const errorText = (name: string) => {
    const message = fieldErrors[name];
    if (!message) return null;
    return Array.isArray(message) ? message.join(" ") : message;
  };
  function updateField(name: string, value: boolean | string | null) {
    setHistory((current) => current ? { ...current, [name]: value } : current);
    setFieldErrors((current) => ({ ...current, [name]: undefined }));
    setError("");
  }
  return (
    <div className="workspace-page co-mx-auto co-max-w-[1560px]">
      <div className="workspace-page-header"><div><h1>Antecedentes de {patient.nombre} {patient.appat}</h1></div></div>
      <p className="clinical-page-description">Sin registrar indica que la respuesta aún no está documentada.</p>
      {history.id !== null && <p className="workspace-inline-warning">En registros anteriores a esta actualización, las respuestas «No» podrían proceder de valores predeterminados. Confirma los antecedentes antes de utilizarlos.</p>}
      <form onSubmit={submit}><fieldset className="clinical-form-fieldset" disabled={saving}>
        {questionGroups.map(({ title, items }) => (
        <fieldset className="history-grid co-mb-4" key={title}>
          <legend className="form-section-heading">{title}</legend>
          {items.map(([name, label]) => (
            <fieldset className="history-question" key={name}>
                  <legend>{label}</legend>
                  <div className="history-choice" role="group" aria-label={label}>
                    <input className="clinical-radio-input" type="radio" id={`${name}-unknown`} name={name} checked={history[name] == null} aria-invalid={Boolean(fieldErrors[name])} aria-describedby={fieldErrors[name] ? `${name}-error` : undefined} onChange={() => updateField(name, null)} />
                    <label className="clinical-radio-choice is-unknown" htmlFor={`${name}-unknown`}>Sin registrar</label>
                    <input
                      className="clinical-radio-input"
                      type="radio"
                      id={`${name}-yes`}
                      name={name}
                      checked={history[name] === true}
                      aria-invalid={Boolean(fieldErrors[name])}
                      aria-describedby={fieldErrors[name] ? `${name}-error` : undefined}
                      onChange={() => updateField(name, true)}
                    />
                    <label
                      className="clinical-radio-choice is-yes"
                      htmlFor={`${name}-yes`}
                    >
                      Sí
                    </label>
                    <input
                      className="clinical-radio-input"
                      type="radio"
                      id={`${name}-no`}
                      name={name}
                      checked={history[name] === false}
                      aria-invalid={Boolean(fieldErrors[name])}
                      aria-describedby={fieldErrors[name] ? `${name}-error` : undefined}
                      onChange={() => updateField(name, false)}
                    />
                    <label
                      className="clinical-radio-choice is-no"
                      htmlFor={`${name}-no`}
                    >
                      No
                    </label>
                  </div>
                  {fieldErrors[name] && (
                    <div id={`${name}-error`} className="clinical-form-field-error history-question-error">
                      {errorText(name)}
                    </div>
                  )}
            </fieldset>
          ))}
        </fieldset>))}
        <section className="history-notes" aria-label="Notas médicas">
            <div className="history-notes-grid">
              {texts.map(([name, label]) => (
                <div key={name}>
                  <label htmlFor={name} className="clinical-form-label">
                    {label}
                  </label>
                  <textarea
                    id={name}
                    className="clinical-form-control"
              rows={3}
                    aria-invalid={Boolean(fieldErrors[name])}
                    aria-describedby={fieldErrors[name] ? `${name}-error` : undefined}
                    value={String(history[name] || "")}
                    onChange={(e) => updateField(name, e.target.value)}
                  />
                  {fieldErrors[name] && (
                    <div id={`${name}-error`} className="clinical-form-field-error">
                      {errorText(name)}
                    </div>
                  )}
                </div>
              ))}
            </div>
        </section>
        <div className="clinical-form-actions">
          <button className="clinical-form-submit" disabled={saving}>
            {saving ? "Guardando…" : "Guardar antecedentes"}
          </button>
        </div>
      </fieldset></form>{guard.prompt}
    </div>
  );
}
