import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../../api/client";

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
export default function MedicalHistoryPage() {
  const { id } = useParams();
  const [history, setHistory] = useState(null);
  const [patient, setPatient] = useState(null);
  const [notice, setNotice] = useState("");
  useEffect(() => {
    Promise.all([
      api(`patients/${id}/`),
      api(`patients/${id}/medical-history/`),
    ]).then(([p, h]) => {
      setPatient(p);
      setHistory(h);
    });
  }, [id]);
  if (!history || !patient)
    return (
      <div className="page-loader">
        <div className="spinner-border text-primary" />
      </div>
    );
  async function submit(e) {
    e.preventDefault();
    setHistory(
      await api(`patients/${id}/medical-history/`, {
        method: "PUT",
        body: JSON.stringify(history),
      }),
    );
    setNotice("Antecedentes actualizados");
  }
  return (
    <div className="container py-4">
      <h1 className="h2">
        Antecedentes de {patient.nombre} {patient.appat}
      </h1>
      {notice && <div className="alert alert-success">{notice}</div>}
      <form onSubmit={submit}>
        <div className="row g-3 my-2">
          {questions.map(([name, label]) => (
            <div className="col-md-6" key={name}>
              <div className="card border-0 shadow-sm h-100">
                <div className="card-body">
                  <p className="fw-semibold">{label}</p>
                  <div className="btn-group" role="group">
                    <input
                      className="btn-check"
                      type="radio"
                      id={`${name}-yes`}
                      checked={history[name] === true}
                      onChange={() => setHistory({ ...history, [name]: true })}
                    />
                    <label
                      className="btn btn-outline-success"
                      htmlFor={`${name}-yes`}
                    >
                      Sí
                    </label>
                    <input
                      className="btn-check"
                      type="radio"
                      id={`${name}-no`}
                      checked={history[name] === false}
                      onChange={() => setHistory({ ...history, [name]: false })}
                    />
                    <label
                      className="btn btn-outline-secondary"
                      htmlFor={`${name}-no`}
                    >
                      No
                    </label>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
        <div className="card border-0 shadow-sm">
          <div className="card-body">
            <div className="row g-3">
              {texts.map(([name, label]) => (
                <div className="col-md-6" key={name}>
                  <label htmlFor={name} className="form-label">
                    {label}
                  </label>
                  <textarea
                    id={name}
                    className="form-control"
                    rows="3"
                    value={history[name] || ""}
                    onChange={(e) =>
                      setHistory({ ...history, [name]: e.target.value })
                    }
                  />
                </div>
              ))}
            </div>
            <button className="btn btn-primary mt-4">
              Guardar antecedentes
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
