import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api, getErrorMessage } from '../api/client';
import { noticeFields } from '../types/compliance';
import type { Notice } from '../types/compliance';

export default function PrivacyPage() {
  const { clinicSlug } = useParams();
  const [result, setResult] = useState<{ configured: boolean; notice: Notice | null } | null>(null);
  const [error, setError] = useState('');
  useEffect(() => {
    let live = true;
    api<{ configured: boolean; notice: Notice | null }>(clinicSlug ? `privacy/${encodeURIComponent(clinicSlug)}/` : 'clinics/privacy/').then((data) => { if (live) setResult(data); }).catch((reason) => { if (live) setError(getErrorMessage(reason)); });
    return () => { live = false; };
  }, [clinicSlug]);
  return <main id="main-content" className="workspace-page privacy-workspace co-mx-auto co-max-w-[1000px]">
    <h1>Aviso de Privacidad</h1>
    {error ? <p role="alert">{error}</p> : !result ? <p role="status">Cargando aviso…</p> : !result.configured || !result.notice ? <section className="workspace-inline-error"><h2>Aviso pendiente de configuración</h2><p>La clínica aún no ha publicado un aviso con los datos de su responsable. Solicita el aviso y el contacto de privacidad antes de proporcionar información personal.</p></section> : <article className="workspace-section">
      <p>Versión {result.notice.version} · Publicado el {new Date(result.notice.published_at).toLocaleDateString('es-MX')}</p>
      {noticeFields.map(([key, label]) => <section key={key}><h2>{label}</h2><p style={{ whiteSpace: 'pre-wrap' }}>{result.notice!.body[key]}</p></section>)}
    </article>}
    {!clinicSlug && <Link to="/">Volver al espacio de trabajo</Link>}
  </main>;
}
