import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../../api/client";

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
  const { id } = useParams();
  const [consent, setConsent] = useState(null);
  const [accepted, setAccepted] = useState(false);
  const [file, setFile] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => {
    api(`patients/${id}/consent/`).then(setConsent);
  }, [id]);
  if (!consent)
    return (
      <div className="page-loader">
        <div className="spinner-border text-primary" />
      </div>
    );
  async function submit(e) {
    e.preventDefault();
    const data = new FormData();
    data.append("texto", clauses.join("\n"));
    if (file) data.append("archivo_ine", file);
    try {
      setConsent(
        await api(`patients/${id}/consent/`, { method: "POST", body: data }),
      );
    } catch (err) {
      setError(err.payload?.archivo_ine?.join(" ") || err.message);
    }
  }
  return (
    <div className="container py-4">
      <div className="card border-0 shadow-sm mx-auto consent-card">
        <div className="card-body p-5">
          <h1 className="text-center">Consentimiento Informado</h1>
          <p className="text-center text-muted">
            Documento de autorización para tratamiento odontológico
          </p>
          <p className="fw-bold">
            Declaro en pleno uso de mis facultades mentales, libre y
            responsablemente:
          </p>
          <ul>
            {clauses.map((clause) => (
              <li className="mb-2" key={clause}>
                {clause}
              </li>
            ))}
          </ul>
          {consent.fecha_aceptacion ? (
            <div className="alert alert-success">
              <h2 className="h5">Consentimiento aceptado</h2>
              <p>{new Date(consent.fecha_aceptacion).toLocaleString()}</p>
              {consent.archivo_ine_url && (
                <a
                  href={consent.archivo_ine_url}
                  target="_blank"
                  rel="noreferrer"
                  className="btn btn-sm btn-outline-success"
                >
                  Ver identificación
                </a>
              )}
            </div>
          ) : (
            <form onSubmit={submit}>
              <div className="form-check p-3 border rounded mb-3">
                <input
                  id="accept-consent"
                  type="checkbox"
                  className="form-check-input"
                  checked={accepted}
                  onChange={(e) => setAccepted(e.target.checked)}
                />
                <label
                  htmlFor="accept-consent"
                  className="form-check-label ms-2"
                >
                  He leído y acepto los términos.
                </label>
              </div>
              <label htmlFor="ine" className="form-label">
                Identificación oficial
              </label>
              <input
                id="ine"
                type="file"
                required
                disabled={!accepted}
                accept="image/*,application/pdf"
                className="form-control"
                onChange={(e) => setFile(e.target.files[0])}
              />
              <small className="text-muted">
                JPG, PNG, GIF o PDF; máximo 5 MB.
              </small>
              {error && <div className="alert alert-danger mt-3">{error}</div>}
              <button
                disabled={!accepted || !file}
                className="btn btn-primary d-block mx-auto mt-4"
              >
                Aceptar y guardar
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
