import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../../api/client";

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
function ImageField({ name, label, required, url, onFile }) {
  return (
    <div className="col-md-6 col-lg-4">
      <div className="card h-100">
        <div className="card-body">
          <label htmlFor={name} className="form-label fw-semibold">
            {label}
          </label>
          {url && <img src={url} alt={label} className="study-preview mb-2" />}
          <input
            id={name}
            type="file"
            accept="image/*"
            required={required && !url}
            className="form-control"
            onChange={(e) => onFile(name, e.target.files[0])}
          />
        </div>
      </div>
    </div>
  );
}
export default function ComparativeStudyPage() {
  const { id } = useParams();
  const [study, setStudy] = useState(null);
  const [files, setFiles] = useState({});
  const [notice, setNotice] = useState("");
  const [errors, setErrors] = useState({});
  useEffect(() => {
    api(`patients/${id}/comparative-study/`).then(setStudy);
  }, [id]);
  if (!study)
    return (
      <div className="page-loader">
        <div className="spinner-border text-primary" />
      </div>
    );
  async function submit(e) {
    e.preventDefault();
    setErrors({});
    const data = new FormData(e.currentTarget);
    Object.entries(files).forEach(
      ([name, file]) => file && data.set(name, file),
    );
    try {
      setStudy(
        await api(`patients/${id}/comparative-study/`, {
          method: "PUT",
          body: data,
        }),
      );
      setFiles({});
      setNotice("Estudio guardado correctamente.");
    } catch (error) {
      setErrors(error.payload || { detail: error.message });
    }
  }
  return (
    <div className="container py-4">
      <div className="d-flex justify-content-between">
        <h1 className="h2">Estudio comparativo</h1>
        {study.exists && (
          <a
            className="btn btn-outline-primary"
            href={`/api/v1/patients/${id}/comparative-study/pdf/`}
          >
            <i className="bi bi-file-pdf me-2" />
            Descargar PDF
          </a>
        )}
      </div>
      {notice && <div className="alert alert-success mt-3">{notice}</div>}
      <form onSubmit={submit}>
        <div className="card border-0 shadow-sm my-4">
          <div className="card-body">
            <div className="row g-3">
              <div className="col-md-4">
                <label htmlFor="fecha_inicio" className="form-label">
                  Fecha de inicio
                </label>
                <input
                  id="fecha_inicio"
                  name="fecha_inicio"
                  type="date"
                  required
                  className="form-control"
                  defaultValue={study.fecha_inicio || ""}
                />
              </div>
              <div className="col-md-8">
                <label htmlFor="diagnostico" className="form-label">
                  Diagnóstico
                </label>
                <input
                  id="diagnostico"
                  name="diagnostico"
                  className="form-control"
                  defaultValue={study.diagnostico || ""}
                />
              </div>
              <div className="col-12">
                <label htmlFor="observaciones" className="form-label">
                  Observaciones
                </label>
                <textarea
                  id="observaciones"
                  name="observaciones"
                  className="form-control"
                  defaultValue={study.observaciones || ""}
                />
              </div>
            </div>
          </div>
        </div>
        <h2 className="h4">Imágenes antes</h2>
        <div className="row g-3 mb-4">
          {before.map(([name, label]) => (
            <ImageField
              key={name}
              name={name}
              label={label}
              required={!study.exists}
              url={study.image_urls?.[name]}
              onFile={(n, f) => setFiles({ ...files, [n]: f })}
            />
          ))}
        </div>
        <h2 className="h4">Imágenes después</h2>
        <div className="row g-3 mb-4">
          {after.map(([name, label]) => (
            <ImageField
              key={name}
              name={name}
              label={label}
              url={study.image_urls?.[name]}
              onFile={(n, f) => setFiles({ ...files, [n]: f })}
            />
          ))}
        </div>
        {Object.keys(errors).length > 0 && (
          <div className="alert alert-danger">
            Verifica los campos e imágenes requeridas.
          </div>
        )}
        <button className="btn btn-primary">Guardar estudio</button>
      </form>
    </div>
  );
}
