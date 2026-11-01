import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";

function AppointmentTable({ appointments, future = false }) {
  if (!appointments.length)
    return (
      <div className="text-center py-5 text-muted">
        <i className="bi bi-calendar-x display-1 opacity-50 d-block" />
        <h5>No hay {future ? "próximas " : ""}citas</h5>
      </div>
    );
  return (
    <div className="table-responsive">
      <table className="table table-hover mb-0">
        <thead>
          <tr>
            {future && <th>Fecha</th>}
            <th>Hora</th>
            <th>Paciente</th>
            <th>Motivo</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody>
          {appointments.map((item) => (
            <tr key={item.id}>
              {future && <td>{item.fecha}</td>}
              <td>
                <span className="badge bg-primary">
                  {item.hora.slice(0, 5)}
                </span>
              </td>
              <td>
                {item.paciente.nombre} {item.paciente.appat}
              </td>
              <td>{item.motivo}</td>
              <td>{item.estatus}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => {
    api("dashboard/")
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);
  if (error)
    return (
      <div className="container py-4">
        <div className="alert alert-danger">{error}</div>
      </div>
    );
  if (!data)
    return (
      <div className="page-loader">
        <div className="spinner-border text-primary" />
      </div>
    );
  return (
    <div className="container-fluid px-4 py-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h2>
            Bienvenido,{" "}
            <span className="text-primary">
              Dr. {user.username.toUpperCase()}
            </span>
          </h2>
          <p className="text-muted">Panel principal del consultorio dental</p>
        </div>
        <Link to="/appointments" className="btn btn-primary">
          <i className="bi bi-plus-circle me-2" />
          Nueva Cita
        </Link>
      </div>
      <div className="row g-3 mb-4">
        <div className="col-md-6">
          <div className="card shadow-sm border-0 h-100">
            <div className="card-body">
              <p className="text-muted text-uppercase small fw-semibold">
                Pacientes
              </p>
              <h3>{data.patient_count}</h3>
              <Link to="/patients">
                Gestionar pacientes <i className="bi bi-arrow-right" />
              </Link>
            </div>
          </div>
        </div>
        <div className="col-md-6">
          <div className="card shadow-sm border-0 h-100">
            <div className="card-body">
              <p className="text-muted text-uppercase small fw-semibold">
                Citas hoy
              </p>
              <h3>{data.today.length}</h3>
              <span className="text-success">Agenda del día</span>
            </div>
          </div>
        </div>
      </div>
      <div className="card border-0 shadow-sm mb-4">
        <div className="card-header bg-white py-3">
          <h5 className="mb-0">Agenda de Hoy</h5>
        </div>
        <AppointmentTable appointments={data.today} />
      </div>
      <div className="card border-0 shadow-sm">
        <div className="card-header bg-white py-3">
          <h5 className="mb-0">Próximas Citas</h5>
        </div>
        <AppointmentTable appointments={data.upcoming} future />
      </div>
    </div>
  );
}
