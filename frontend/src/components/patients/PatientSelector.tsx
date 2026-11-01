import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import type { PatientOption } from "../../types/domain";
import { patientsService } from "../../services/patients";
import { queryKeys } from "../../query/keys";

export default function PatientSelector({ onSelect }: { onSelect: (patient: PatientOption) => void }) {
  const [term, setTerm] = useState("");
  const [debouncedTerm, setDebouncedTerm] = useState(term);
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedTerm(term), 250);
    return () => clearTimeout(timer);
  }, [term]);
  const query = useQuery({
    queryKey: queryKeys.patientAutocomplete(debouncedTerm),
    queryFn: () => patientsService.autocomplete(debouncedTerm),
    enabled: debouncedTerm === term,
  });
  const results = query.data?.results ?? [];
  const error = query.error?.message ?? "";
  const loading = debouncedTerm !== term || query.isPending;
  return (
    <div>
      <label htmlFor="patient-selector" className="clinical-form-label">
        Buscar paciente por nombre, apellido, teléfono o ID
      </label>
      <input
        id="patient-selector"
        type="search"
        className="clinical-form-control"
        value={term}
        onChange={(e) => setTerm(e.target.value)}
        autoComplete="off"
        aria-controls="patient-selector-results"
        aria-busy={loading}
      />
      {error && <div className="clinical-form-field-error" role="alert">{error}</div>}
      {loading && <div className="clinical-loading-note co-mt-2" role="status">Buscando pacientes…</div>}
      <div
        className="patient-selector-results"
        id="patient-selector-results"
        role="group"
        aria-label="Resultados de pacientes"
        aria-live="polite"
        aria-busy={loading}
      >
        {results.map((patient) => (
          <button
            type="button"
            className="patient-selector-option"
            key={patient.id}
            onClick={() => onSelect(patient)}
          >
            {patient.text} <span>· ID {patient.id}</span>
          </button>
        ))}
      </div>
      {!loading && !error && term.trim() && results.length === 0 && (
        <p className="clinical-loading-note co-mt-2" role="status">No se encontraron pacientes.</p>
      )}
    </div>
  );
}
