import { Link, useParams } from "react-router-dom";
import { useResource } from "../../hooks/useResource";
import type { Consultation } from "../../types/domain";
import { useState } from 'react';
import { api, getErrorMessage } from '../../api/client';
import { useAuth } from '../../context/AuthContext';

export default function PrescriptionPage() {
  const { id } = useParams();
  const { data, error, reload } = useResource<Consultation>(`consultations/${id}/`);
  const [updated, setUpdated] = useState<Consultation | null>(null);
  const item = updated || data;
  const { user } = useAuth();
  const [form, setForm] = useState({ password: '', code: '', text: '' });
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  async function attest(operation: 'close' | 'addendum') {
    if (busy) return;
    setBusy(true); setMessage('');
    try { const result = await api<Consultation>(`clinics/consultations/${id}/${operation}/`, { method: 'POST', body: JSON.stringify(form) }); setUpdated(result); setForm({ password: '', code: '', text: '' }); }
    catch (reason) { setMessage(getErrorMessage(reason)); }
    finally { setBusy(false); }
  }
  if (error)
    return <div className="workspace-page co-mx-auto co-max-w-[1320px]"><div className="workspace-inline-error" role="alert">{error}</div><button className="clinical-action-outline co-mt-3" onClick={reload}>Reintentar</button></div>;
  if (!item)
    return (
      <div className="page-loader" role="status" aria-label="Cargando receta">
        <div className="workspace-loader-spinner" />
      </div>
    );
  return (
    <div className="workspace-page co-mx-auto co-max-w-[1320px]">
      <div className="prescription-context">Consulta #{item.id}</div>
      <article className="prescription-sheet">
          <h1>Receta médica</h1>
          <p>{item.status === 'CLOSED' ? `Documento cerrado · ${item.author_name}` : item.status === 'DRAFT' ? 'Borrador pendiente de cierre' : 'Documento histórico sin cierre acreditado'}</p>
          {item.integrity === 'invalid' && <p role="alert">La integridad del documento requiere revisión. No utilizar como documento validado.</p>}
          <div className="prescription-patient">
          <p>
            <strong>Paciente:</strong> {item.paciente.full_name}
          </p>
          <p>
            <strong>Fecha:</strong>{" "}
            {new Date(item.fecha_consulta).toLocaleString("es-MX")}
          </p>
          </div>
          <h2>Diagnóstico</h2>
          <p>{item.diagnostico}</p>
          <h2>Tratamiento</h2>
          <p>{item.tratamiento}</p>
          <h2>Observaciones</h2>
          <p>{item.observaciones}</p>
          {item.addenda?.map((row) => <section key={row.id}><h2>Adenda</h2><p>{row.author_name} · {new Date(row.created_at).toLocaleString('es-MX')} · {row.integrity === 'verified' ? 'Integridad verificada' : 'Requiere revisión'}</p><p style={{ whiteSpace: 'pre-wrap' }}>{row.text}</p></section>)}
      </article>
      {(item.status === 'DRAFT' || item.status === 'LEGACY' || (item.status === 'CLOSED' && item.integrity === 'verified')) && <section className="workspace-section print-hidden"><h2>{item.status === 'DRAFT' ? 'Cerrar documento' : 'Agregar adenda'}</h2><p>El cierre vincula el contenido con tu identidad autenticada y evita su modificación ordinaria. No equivale a firma electrónica avanzada. Una adenda histórica no acredita la firma del documento original.</p>
        {item.status !== 'DRAFT' && <><label htmlFor="addendum-text">Corrección o aclaración</label><textarea id="addendum-text" className="clinical-form-control" value={form.text} minLength={10} onChange={(event) => setForm({ ...form, text: event.target.value })} /></>}
        <label htmlFor="document-password">Confirma tu contraseña</label><input id="document-password" className="clinical-form-control" type="password" autoComplete="current-password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} />
        {user?.mfa_enabled && <><label htmlFor="document-code">Código del autenticador</label><input id="document-code" className="clinical-form-control" autoComplete="one-time-code" value={form.code} onChange={(event) => setForm({ ...form, code: event.target.value })} /></>}
        {message && <p role="alert">{message}</p>}<button className="clinical-action-primary" disabled={busy || !form.password || (item.status !== 'DRAFT' && form.text.trim().length < 10)} onClick={() => void attest(item.status === 'DRAFT' ? 'close' : 'addendum')}>{busy ? 'Guardando…' : item.status === 'DRAFT' ? 'Confirmar cierre' : 'Guardar adenda'}</button><p><Link to="/security">Revisar mi nombre y seguridad</Link></p>
      </section>}
      <div className="co-flex co-flex-wrap co-gap-3 co-mt-4 print-hidden">
        <Link className="clinical-action-outline" to={`/patients/${item.paciente.id}`}>Ver paciente</Link>
        <Link className="clinical-action-outline" to={`/patients/${item.paciente.id}/consultations`}>Historial de consultas</Link>
      </div>
      <button
        className="clinical-action-primary co-mt-4 print-hidden"
        type="button"
        disabled={item.status === 'DRAFT' || item.integrity === 'invalid'}
        onClick={() => window.print()}
      >
        <i className="bi bi-printer" aria-hidden="true" />
        Descargar PDF / Imprimir
      </button>
    </div>
  );
}
