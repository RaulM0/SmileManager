import { useState } from 'react';

export type FieldGuidance = { what: string; purpose: string; example?: string };

export default function FieldLabelHelp({ htmlFor, label, guidance }: { htmlFor: string; label: string; guidance: FieldGuidance }) {
  const [open, setOpen] = useState(false);
  const helpId = `${htmlFor}-help`;
  return <>
    <div className="field-label-help">
      <label className="clinical-form-label" htmlFor={htmlFor}>{label}</label>
      <button type="button" className="field-help-toggle" aria-label={`Información sobre ${label}`} aria-expanded={open} aria-controls={helpId} onClick={() => setOpen(!open)}>
        <i className="bi bi-info-circle" aria-hidden="true" />
      </button>
    </div>
    <div id={helpId} className="field-help-panel" hidden={!open}>
      <p><strong>Qué agregar:</strong> {guidance.what}</p>
      <p><strong>Para qué sirve:</strong> {guidance.purpose}</p>
      {guidance.example && <p><strong>Ejemplo:</strong> {guidance.example}</p>}
    </div>
  </>;
}
