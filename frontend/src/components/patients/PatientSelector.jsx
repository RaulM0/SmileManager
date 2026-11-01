import { useEffect, useState } from "react";
import { api } from "../../api/client";

export default function PatientSelector({ onSelect }) {
  const [term, setTerm] = useState("");
  const [results, setResults] = useState([]);
  const [error, setError] = useState("");
  useEffect(() => {
    const timer = setTimeout(() => {
      api(`patients/autocomplete/?term=${encodeURIComponent(term)}`)
        .then((data) => setResults(data.results))
        .catch((e) => setError(e.message));
    }, 250);
    return () => clearTimeout(timer);
  }, [term]);
  return (
    <div>
      <label htmlFor="patient-selector" className="form-label">
        Buscar paciente por nombre
      </label>
      <input
        id="patient-selector"
        className="form-control"
        value={term}
        onChange={(e) => setTerm(e.target.value)}
        autoComplete="off"
      />
      {error && <div className="text-danger small mt-2">{error}</div>}
      <div className="list-group mt-2">
        {results.map((patient) => (
          <button
            type="button"
            className="list-group-item list-group-item-action"
            key={patient.id}
            onClick={() => onSelect(patient)}
          >
            {patient.text}
          </button>
        ))}
      </div>
    </div>
  );
}
