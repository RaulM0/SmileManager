import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { useParams } from 'react-router-dom';
import { api, getErrorMessage, getFormErrors } from '../../api/client';
import { useToast } from '../../context/ToastContext';
import type { ConsentWorkspace } from '../../types/compliance';
import { clinicalService } from '../../services/clinical';
import { useUnsavedChanges } from '../../hooks/useUnsavedChanges';
import { useApiDownload } from '../../hooks/useApiDownload';
import { ConfirmDialog } from '../../components/ConfirmDialog';

export default function ConsentPage() {
  const { id } = useParams();
  const toast = useToast();
  const [workspace, setWorkspace] = useState<ConsentWorkspace | null>(null);
  const [form, setForm] = useState({ template_id: '', signer_name: '', signer_role: 'PATIENT', representative_basis: '', signed_on: '', supersedes_id: '' });
  const [attested, setAttested] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState('');
  const [documentError, setDocumentError] = useState('');
  const [saving, setSaving] = useState(false);
  const [reload, setReload] = useState(0);
  const [revoking, setRevoking] = useState<number | null>(null);
  const [reason, setReason] = useState('');
  const guard = useUnsavedChanges(Boolean(file || form.signer_name || attested));
  const { active: downloadActive, download } = useApiDownload();
  useEffect(() => {
    let live = true;
    clinicalService.consent(id!).then((data) => { if (live) { setWorkspace(data); setError(''); } }).catch((requestError) => { if (live) setError(getErrorMessage(requestError)); });
    return () => { live = false; };
  }, [id, reload]);
  const selected = workspace?.templates.find((row) => String(row.id) === form.template_id) || workspace?.templates[0];
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (saving || !selected || !file) return;
    setSaving(true); setError(''); setDocumentError('');
    const data = new FormData();
    for (const [key, value] of Object.entries(form)) if (value) data.append(key, value);
    data.set('template_id', String(selected.id));
    data.append('attested', String(attested));
    data.append('signed_document', file);
    try {
      await clinicalService.saveConsent(id!, data);
      guard.markSaved(); setForm({ template_id: '', signer_name: '', signer_role: 'PATIENT', representative_basis: '', signed_on: '', supersedes_id: '' }); setAttested(false); setFile(null); setReload((value) => value + 1);
      toast.success('Evidencia documental registrada.');
    } catch (requestError) {
      const field = getFormErrors<'signed_document'>(requestError).signed_document;
      setDocumentError(Array.isArray(field) ? field.join(' ') : field || '');
      toast.error(Array.isArray(field) ? field.join(' ') : field || getErrorMessage(requestError));
    } finally { setSaving(false); }
  }
  if (!workspace) return <div className="workspace-page">{error ? <><p className="workspace-inline-error" role="alert">{error}</p><button className="clinical-action-outline" onClick={() => setReload((value) => value + 1)}>Reintentar</button></> : <p role="status">Cargando consentimientos…</p>}</div>;
  return <div className="workspace-page consent-workspace co-mx-auto co-max-w-[1320px]">
    <header className="workspace-page-header"><div><h1>Consentimientos y evidencia documental</h1><p className="clinical-page-description">El consentimiento clínico y el tratamiento de datos se registran por separado. La carga conserva un documento firmado; no constituye por sí misma una firma electrónica avanzada ni una validación jurídica.</p></div></header>
    {error && <p role="alert" className="workspace-inline-error">{error}</p>}
    {workspace.legacy && <section className="workspace-section"><div className="workspace-section-heading"><h2>Registro histórico sin firma verificada</h2></div><div className="consent-section-body"><p>La fecha de aceptación del flujo anterior no acredita por sí misma la voluntad del paciente. Este registro se conserva para revisión.</p><p style={{ whiteSpace: 'pre-wrap' }}>{workspace.legacy.texto}</p>
      {workspace.legacy.pdf_generado && <button className="clinical-action-outline" disabled={Boolean(downloadActive)} onClick={() => void download('legacy-pdf', `clinics/patients/${id}/consent/pdf/file/`, `Historico_${id}.pdf`)}>Descargar documento histórico</button>}
      {workspace.legacy.archivo_ine_url && <button className="clinical-action-outline" disabled={Boolean(downloadActive)} onClick={() => void download('legacy-identity', `clinics/patients/${id}/consent/identity/file/`, `Identificacion_historica_${id}`)}>Descargar identificación histórica</button>}
    </div></section>}
    {!selected ? <section className="consent-configuration-notice" aria-labelledby="consent-configuration-heading"><i className="bi bi-info-circle" aria-hidden="true" /><div><h2 id="consent-configuration-heading">Registro pendiente de configuración</h2><p>La administración debe publicar el aviso de privacidad y las plantillas revisadas antes de incorporar documentos nuevos.</p></div></section> : <form className="workspace-section consent-form" onSubmit={submit}>
      <div className="workspace-section-heading"><div><h2>Registrar documento firmado</h2><p>Completa los datos del firmante y adjunta la evidencia documental.</p></div></div><div className="consent-section-body">
      <label className="clinical-form-label" htmlFor="consent-template">Plantilla aprobada</label><select id="consent-template" className="clinical-form-control" value={String(selected.id)} onChange={(event) => setForm({ ...form, template_id: event.target.value, supersedes_id: '' })}>{workspace.templates.map((row) => <option key={row.id} value={row.id}>{row.kind === 'CLINICAL' ? 'Clínico' : 'Datos personales'} · {row.title} · versión {row.version}</option>)}</select>
      <p className="consent-template-preview">{selected.text}</p>
      <label className="clinical-form-label" htmlFor="consent-signer">Nombre completo del firmante</label><input id="consent-signer" className="clinical-form-control" required minLength={3} maxLength={300} value={form.signer_name} onChange={(event) => setForm({ ...form, signer_name: event.target.value })} />
      <label className="clinical-form-label" htmlFor="consent-role">Calidad del firmante</label><select id="consent-role" className="clinical-form-control" value={form.signer_role} onChange={(event) => setForm({ ...form, signer_role: event.target.value })}><option value="PATIENT">Paciente</option><option value="REPRESENTATIVE">Representante</option></select>
      {form.signer_role === 'REPRESENTATIVE' && <><label className="clinical-form-label" htmlFor="consent-basis">Representación y evidencia que la acredita</label><textarea id="consent-basis" className="clinical-form-control" required minLength={10} value={form.representative_basis} onChange={(event) => setForm({ ...form, representative_basis: event.target.value })} /></>}
      <label className="clinical-form-label" htmlFor="consent-date">Fecha de firma</label><input id="consent-date" type="date" className="clinical-form-control" required value={form.signed_on} onChange={(event) => setForm({ ...form, signed_on: event.target.value })} />
      <label className="clinical-form-label" htmlFor="signed-document">Documento firmado completo</label><input id="signed-document" type="file" className="clinical-form-control" required accept=".pdf,.jpg,.jpeg,.png,.gif,.webp" aria-invalid={Boolean(documentError)} aria-describedby={documentError ? 'document-help document-error' : 'document-help'} onChange={(event) => { setFile(event.target.files?.[0] || null); setDocumentError(''); }} /><small className="clinical-form-help" id="document-help">PDF, JPG, PNG, GIF o WEBP; máximo 5 MB. El documento original se conserva sin reconstruirlo.</small>
      {documentError && <p id="document-error" className="clinical-form-field-error">{documentError}</p>}
      <label className="clinical-form-label" htmlFor="consent-supersedes">Sustituye un documento anterior (opcional)</label><select id="consent-supersedes" className="clinical-form-control" value={form.supersedes_id} onChange={(event) => setForm({ ...form, supersedes_id: event.target.value })}><option value="">No sustituye otro documento</option>{workspace.records.filter((row) => row.template.kind === selected.kind && !row.revoked_at && !row.superseded).map((row) => <option key={row.id} value={row.id}>Documento #{row.id} · {row.signed_on}</option>)}</select>
      <label className="consent-attestation"><input type="checkbox" checked={attested} required onChange={(event) => setAttested(event.target.checked)} /> Verifiqué el documento firmado, su correspondencia con esta plantilla y la identidad o representación del firmante.</label>
      <div className="consent-form-actions"><button className="clinical-form-submit" disabled={saving || !file || !attested}>{saving ? 'Guardando…' : 'Registrar evidencia'}</button></div></div>
    </form>}
    <section className="workspace-section"><div className="workspace-section-heading"><div><h2>Documentos registrados</h2><p>Evidencias documentales del paciente</p></div></div>{workspace.records.length === 0 && <div className="workspace-empty-state"><i className="bi bi-file-earmark-text" aria-hidden="true" /><span>No hay evidencias registradas con el nuevo procedimiento.</span></div>}{workspace.records.map((row) => <article key={row.id} className="consent-record"><h3>Documento #{row.id} · {row.template.title}</h3><p>{row.signer_name} · firmado el {row.signed_on} · registrado por {row.recorded_name}</p><p>Integridad: {row.integrity === 'verified' ? 'Verificada' : 'Requiere revisión'}{row.revoked_at ? ' · Revocación registrada' : row.superseded ? ' · Sustituido' : ''}</p>{row.revocation_reason && <p>{row.revocation_reason}</p>}
      <button className="clinical-action-outline" disabled={Boolean(downloadActive) || row.integrity !== 'verified' || (Boolean(row.scan_status) && !['CLEAN', 'NOT_REQUIRED'].includes(row.scan_status!))} onClick={() => void download(`evidence-${row.id}`, `clinics/patients/${id}/consent/records/${row.id}/file/`, `Consentimiento_${row.id}`)}>Descargar documento #{row.id}</button>
      {row.scan_status && !['CLEAN', 'NOT_REQUIRED'].includes(row.scan_status) && <p role="status">{row.scan_status === 'REJECTED' ? 'Documento bloqueado por la revisión de seguridad.' : 'Documento en cuarentena. Actualiza la página para consultar la revisión.'}</p>}
      {!row.revoked_at && <button className="clinical-action-outline" disabled={saving} onClick={() => { setRevoking(row.id); setReason(''); }}>Registrar revocación #{row.id}</button>}
    </article>)}</section>
    {revoking !== null && <ConfirmDialog title="Registrar revocación" confirmLabel="Guardar revocación" busy={saving} onClose={() => setRevoking(null)} onConfirm={async () => { if (reason.trim().length < 10) { toast.warning('Describe la solicitud y su motivo con al menos 10 caracteres.'); return; } setSaving(true); try { await api(`clinics/patients/${id}/consent/records/${revoking}/revoke/`, { method: 'POST', body: JSON.stringify({ reason }) }); setRevoking(null); toast.success('Revocación registrada.'); setReload((value) => value + 1); } catch (requestError) { toast.error(getErrorMessage(requestError)); } finally { setSaving(false); } }}><p>Se conservarán el documento y la trazabilidad. Esta acción no borra el expediente ni sustituye la atención de una solicitud ARCO.</p><label className="clinical-form-label" htmlFor="revocation-reason">Solicitud y motivo</label><textarea id="revocation-reason" className="clinical-form-control" minLength={10} value={reason} onChange={(event) => setReason(event.target.value)} /></ConfirmDialog>}
    {guard.prompt}
  </div>;
}
