import { useToast } from "../context/ToastContext";
import { useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, getClinicContext, getErrorMessage } from "../api/client";
import type { Paginated } from "../types/domain";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { useUnsavedChanges } from "../hooks/useUnsavedChanges";

type Patient = { id: number; name: string; doctor: string };
type Appointment = { id: number; patient: Patient; fecha: string; hora: string; motivo: string; estatus: "P" | "C" | "A" };
const empty = { paciente_id: "", fecha: "", hora: "10:00", motivo: "" };
const stateLabel = { P: "Pendiente", C: "Completada", A: "Anulada" };

export default function StaffAgendaPage() {
  const toast = useToast();
  const clinic = getClinicContext();
  const client = useQueryClient();
  const [term, setTerm] = useState("");
  const [date, setDate] = useState("");
  const [page, setPage] = useState(1);
  const [form, setForm] = useState(empty);
  const [editing, setEditing] = useState<number | null>(null);
  const [transition, setTransition] = useState<{ appointment: Appointment; operation: "complete" | "cancel" } | null>(null);
  const guard = useUnsavedChanges(form.paciente_id !== "" || form.fecha !== "" || form.motivo !== "");
  const key = [clinic, "staff-agenda"];
  const patients = useQuery({ queryKey: [...key, "patients", term], queryFn: () => api<{ results: Patient[] }>(`clinics/staff/patients/?term=${encodeURIComponent(term)}`) });
  const appointments = useQuery({ queryKey: [...key, "appointments", date, page], queryFn: () => api<Paginated<Appointment>>(`clinics/staff/appointments/?page=${page}&date=${date}`) });
  const mutation = useMutation({
    mutationFn: ({ path, method, body }: { path: string; method: string; body?: object }) => api(path, { method, ...(body ? { body: JSON.stringify(body) } : {}) }),
    onSuccess: async (_, variables) => { if (variables.body) { guard.markSaved(); setForm(empty); setEditing(null); } setTransition(null); toast.success("Cita guardada correctamente."); await client.invalidateQueries({ queryKey: key }); },
    onError: error => toast.error(getErrorMessage(error)),
  });
  function save(event: FormEvent) {
    event.preventDefault();
    mutation.mutate({ path: editing ? `clinics/staff/appointments/${editing}/` : "clinics/staff/appointments/", method: editing ? "PATCH" : "POST", body: { ...form, paciente_id: Number(form.paciente_id) } });
  }
  function edit(appointment: Appointment) {
    setEditing(appointment.id);
    setForm({ paciente_id: String(appointment.patient.id), fecha: appointment.fecha, hora: appointment.hora.slice(0, 5), motivo: appointment.motivo });
  }
  const options = patients.data?.results ?? [];
  return <div className="workspace-page co-mx-auto co-max-w-[1320px]">
    {guard.prompt}
    <h1>Agenda de recepción</h1><p>Programa y actualiza citas de la clínica. Los expedientes están reservados al médico asignado.</p>
    <section className="workspace-section"><h2>{editing ? "Editar cita" : "Nueva cita"}</h2>
      <label>Buscar paciente <input value={term} onChange={event => setTerm(event.target.value)} /></label>
      {patients.isError && <p role="alert">No fue posible cargar los pacientes.</p>}
      <form onSubmit={save} className="co-flex co-flex-wrap co-gap-3">
        <label>Paciente <select required value={form.paciente_id} onChange={event => setForm({ ...form, paciente_id: event.target.value })}><option value="">Selecciona un paciente</option>{form.paciente_id && !options.some(p => String(p.id) === form.paciente_id) && <option value={form.paciente_id}>Paciente seleccionado #{form.paciente_id}</option>}{options.map(patient => <option key={patient.id} value={patient.id}>{patient.name} · {patient.doctor}</option>)}</select></label>
        <label>Fecha <input type="date" required value={form.fecha} onChange={event => setForm({ ...form, fecha: event.target.value })} /></label>
        <label>Hora <input type="time" min="08:00" max="20:00" required value={form.hora} onChange={event => setForm({ ...form, hora: event.target.value })} /></label>
        <label>Motivo de la cita <input maxLength={1000} value={form.motivo} onChange={event => setForm({ ...form, motivo: event.target.value })} /></label>
        <button className="clinical-action-primary" disabled={mutation.isPending}>Guardar cita</button>
        {editing && <button type="button" disabled={mutation.isPending} onClick={() => { setEditing(null); setForm(empty); }}>Cancelar edición</button>}
      </form>
    </section>
    <section className="workspace-section"><h2>Citas</h2><label>Filtrar por fecha <input type="date" value={date} onChange={event => { setDate(event.target.value); setPage(1); }} /></label>
      {appointments.isPending ? <p role="status">Cargando agenda…</p> : appointments.isError ? <p role="alert">No fue posible cargar la agenda.</p> : <div className="workspace-table-scroll"><table className="workspace-data-table"><thead><tr><th>Paciente</th><th>Médico</th><th>Fecha</th><th>Hora</th><th>Motivo</th><th>Estado</th><th>Acciones</th></tr></thead><tbody>{appointments.data?.results.map(appointment => <tr key={appointment.id}><td>{appointment.patient.name}</td><td>{appointment.patient.doctor}</td><td>{appointment.fecha}</td><td>{appointment.hora.slice(0, 5)}</td><td>{appointment.motivo}</td><td>{stateLabel[appointment.estatus]}</td><td><button type="button" disabled={mutation.isPending} onClick={() => edit(appointment)}>Editar</button>{appointment.estatus === "P" && <><button type="button" disabled={mutation.isPending} onClick={() => setTransition({ appointment, operation: "complete" })}>Completar</button><button type="button" disabled={mutation.isPending} onClick={() => setTransition({ appointment, operation: "cancel" })}>Anular</button></>}</td></tr>)}</tbody></table>{appointments.data?.results.length === 0 && <p>No hay citas.</p>}<nav className="workspace-pagination" aria-label="Paginación de agenda"><button className="clinical-action-outline clinical-action-compact" disabled={page === 1} onClick={() => setPage(page - 1)}>Anterior</button><span className="workspace-pagination-summary" aria-live="polite">Página {page}</span><button className="clinical-action-outline clinical-action-compact" disabled={!appointments.data?.next} onClick={() => setPage(page + 1)}>Siguiente</button></nav></div>}
    </section>
    {transition && <ConfirmDialog title="Cambiar estado de cita" confirmLabel="Confirmar cambio" busy={mutation.isPending} onClose={() => setTransition(null)} onConfirm={() => mutation.mutate({ path: `clinics/staff/appointments/${transition.appointment.id}/${transition.operation}/`, method: "POST" })}><p>Se cambiará el estado de la cita de {transition.appointment.patient.name}.</p></ConfirmDialog>}
  </div>;
}
