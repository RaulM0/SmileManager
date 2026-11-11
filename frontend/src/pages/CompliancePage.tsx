import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, getClinicContext, getErrorMessage } from '../api/client';
import { noticeFields } from '../types/compliance';
import type { ConsentTemplate, Notice } from '../types/compliance';

export default function CompliancePage() {
  const [body, setBody] = useState<Record<string, string>>(Object.fromEntries(noticeFields.map(([key]) => [key, ''])));
  const [notice, setNotice] = useState<Notice | null>(null);
  const [templates, setTemplates] = useState<ConsentTemplate[]>([]);
  const [reviewed, setReviewed] = useState(false);
  const [templateReviewed, setTemplateReviewed] = useState(false);
  const [template, setTemplate] = useState({ kind: 'CLINICAL', title: '', text: '' });
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [reload, setReload] = useState(0);
  const [loaded, setLoaded] = useState(false);
  const [loadError, setLoadError] = useState('');
  const bodyEdited = useRef(false);
  useEffect(() => {
    if (!getClinicContext()) return;
    let live = true;
    Promise.all([api<{ notice: Notice | null }>('clinics/privacy/'), api<ConsentTemplate[]>('clinics/admin/consent-templates/')]).then(([result, rows]) => {
      if (!live) return;
      setNotice(result.notice);
      if (result.notice && !bodyEdited.current) setBody(result.notice.body);
      setTemplates(rows);
      setLoaded(true);
    }).catch((reason) => { if (live) setLoadError(getErrorMessage(reason)); });
    return () => { live = false; };
  }, [reload]);
  if (!getClinicContext()) return <main className="workspace-page"><h1>Privacidad y consentimientos</h1><p>Selecciona una clínica en el espacio de trabajo para continuar.</p><Link to="/">Volver</Link></main>;
  if (loadError || !loaded) return <main className="workspace-page"><Link to="/">Volver</Link><h1>Privacidad y consentimientos</h1><p role={loadError ? 'alert' : 'status'}>{loadError || 'Cargando configuración de la clínica…'}</p></main>;
  return <main className="workspace-page co-mx-auto co-max-w-[1100px]">
    <Link to="/">Volver al espacio de trabajo</Link><h1>Privacidad y consentimientos</h1>
    <p>Solo la administración de la clínica puede publicar. Cada publicación conserva una versión independiente; confirma la revisión jurídica y clínica antes de continuar.</p>
    {message && <p role="status">{message}</p>}
    <form className="workspace-section" onSubmit={async (event) => { event.preventDefault(); if (busy) return; setBusy(true); try { const result = await api<Notice>('clinics/admin/privacy/', { method: 'POST', body: JSON.stringify({ ...body, review_confirmed: reviewed }) }); setMessage(`Aviso versión ${result.version} publicado.`); setReviewed(false); bodyEdited.current = false; setLoaded(false); setReload((value) => value + 1); } catch (reason) { setMessage(getErrorMessage(reason)); } finally { setBusy(false); } }}>
      <h2>Aviso de privacidad {notice ? `· versión actual ${notice.version}` : 'pendiente de configuración'}</h2>
      {noticeFields.map(([key, label]) => <div className="clinical-form-field" key={key}><label htmlFor={`notice-${key}`}>{label}</label>{key === 'privacy_email' ? <input id={`notice-${key}`} type="email" className="clinical-form-control" required value={body[key]} onChange={(event) => { bodyEdited.current = true; setBody({ ...body, [key]: event.target.value }); }} /> : <textarea id={`notice-${key}`} className="clinical-form-control" required maxLength={key === 'arco_procedure' ? 20000 : 10000} value={body[key]} onChange={(event) => { bodyEdited.current = true; setBody({ ...body, [key]: event.target.value }); }} />}</div>)}
      <label><input type="checkbox" checked={reviewed} required onChange={(event) => setReviewed(event.target.checked)} /> El responsable revisó estos datos y los procedimientos están disponibles para los titulares.</label>
      <button className="clinical-action-primary" disabled={busy || !reviewed}>Publicar nueva versión del aviso</button>
    </form>
    <form className="workspace-section" onSubmit={async (event) => { event.preventDefault(); if (busy) return; setBusy(true); try { await api('clinics/admin/consent-templates/', { method: 'POST', body: JSON.stringify({ ...template, review_confirmed: templateReviewed }) }); setMessage('Nueva versión de plantilla publicada.'); setTemplateReviewed(false); setLoaded(false); setReload((value) => value + 1); } catch (reason) { setMessage(getErrorMessage(reason)); } finally { setBusy(false); } }}>
      <h2>Plantilla de consentimiento</h2><p>El texto debe corresponder al documento que firmará el paciente o representante. La carga posterior registra evidencia documental; no autentica por sí misma al firmante.</p>
      <label htmlFor="template-kind">Tipo</label><select id="template-kind" className="clinical-form-control" value={template.kind} onChange={(event) => setTemplate({ ...template, kind: event.target.value })}><option value="CLINICAL">Clínico</option><option value="PRIVACY">Tratamiento de datos personales</option></select>
      <label htmlFor="template-title">Título</label><input id="template-title" className="clinical-form-control" required maxLength={250} value={template.title} onChange={(event) => setTemplate({ ...template, title: event.target.value })} />
      <label htmlFor="template-text">Texto completo aprobado</label><textarea id="template-text" className="clinical-form-control" rows={12} required minLength={20} maxLength={100000} value={template.text} onChange={(event) => setTemplate({ ...template, text: event.target.value })} />
      <label><input type="checkbox" checked={templateReviewed} required onChange={(event) => setTemplateReviewed(event.target.checked)} /> Se revisaron el contenido, la representación y el procedimiento de documento firmado adjunto.</label>
      <button className="clinical-action-primary" disabled={busy || !templateReviewed || !notice}>Publicar nueva versión de plantilla</button>
    </form>
    <section className="workspace-section"><h2>Versiones publicadas</h2>{templates.map((row) => <p key={row.id}>{row.title} · {row.kind === 'CLINICAL' ? 'Clínico' : 'Datos personales'} · versión {row.version}</p>)}</section>
  </main>;
}
