import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../../api/client";
import AppointmentForm from "../../components/appointments/AppointmentForm";

export default function AppointmentEditPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [item, setItem] = useState(null);
  useEffect(() => {
    api(`appointments/${id}/`).then(setItem);
  }, [id]);
  if (!item)
    return (
      <div className="page-loader">
        <div className="spinner-border text-primary" />
      </div>
    );
  return (
    <div className="container py-4">
      <h1 className="h2 mb-4">Editar cita de {item.paciente.full_name}</h1>
      <AppointmentForm
        initialValue={{ ...item, hora: item.hora.slice(0, 5) }}
        submitLabel="Guardar cambios"
        onSubmit={async (form) => {
          await api(`appointments/${id}/`, {
            method: "PATCH",
            body: JSON.stringify({ ...form, paciente_id: item.paciente.id }),
          });
          navigate(`/appointments/${id}`);
        }}
      />
    </div>
  );
}
