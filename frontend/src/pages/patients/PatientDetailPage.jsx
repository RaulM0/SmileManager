import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../../api/client";

export default function PatientDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [patient, setPatient] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => {
    api(`patients/${id}/`)
      .then(setPatient)
      .catch((e) => setError(e.message));
  }, [id]);
  async function deactivate() {
    if (!window.confirm("¿Deseas desactivar este paciente?")) return;
    await api(`patients/${id}/deactivate/`, { method: "POST" });
    navigate("/patients/search");
  }
  if (error)
    return (
      <div className="container py-4">
        <div className="alert alert-danger">{error}</div>
      </div>
    );
  if (!patient)
    return (
      <div className="page-loader">
        <div className="spinner-border text-primary" />
      </div>
    );
  return (
    <div className="container py-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1>
          {patient.nombre} {patient.appat} {patient.apmat}
        </h1>
        <div>
          <Link className="btn btn-primary me-2" to={`/patients/${id}/edit`}>
            Editar
          </Link>
          <button
            className="btn btn-outline-danger"
            disabled={patient.estatus === "I"}
            onClick={deactivate}
          >
            Desactivar
          </button>
        </div>
      </div>
      <div className="card border-0 shadow-sm">
        <div className="card-body">
          <div className="row g-4">
            <div className="col-md-4">
              <small className="text-muted">Fecha de nacimiento</small>
              <p>
                {patient.fecha_nacimiento} ({patient.age} años)
              </p>
            </div>
            <div className="col-md-4">
              <small className="text-muted">Género</small>
              <p>{patient.genero === "F" ? "Femenino" : "Masculino"}</p>
            </div>
            <div className="col-md-4">
              <small className="text-muted">Estado</small>
              <p>{patient.estatus === "A" ? "Activo" : "Inactivo"}</p>
            </div>
            <div className="col-md-6">
              <small className="text-muted">Teléfono</small>
              <p>{patient.telefono}</p>
            </div>
            <div className="col-md-6">
              <small className="text-muted">Correo</small>
              <p>{patient.email}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
