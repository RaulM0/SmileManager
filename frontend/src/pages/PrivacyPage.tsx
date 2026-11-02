export default function PrivacyPage() {
  return (
    <div className="workspace-page privacy-workspace co-mx-auto">
      <header className="workspace-page-header">
        <div>
          <h1>Aviso de Privacidad</h1>
          <p className="clinical-page-description">Protección de datos personales y clínicos</p>
        </div>
      </header>
      <article className="workspace-section privacy-card">
        <div className="privacy-content">
          <p>
            SmileManager, responsable del tratamiento de sus datos personales,
            pone a su disposición este aviso conforme a la legislación
            aplicable.
          </p>
          <h2>Datos personales recabados</h2>
          <p>
            Podemos recabar datos de identificación, contacto, información
            médica y odontológica, antecedentes clínicos, fotografías,
            radiografías, documentos de identificación y datos relacionados con
            citas y tratamientos.
          </p>
          <h2>Finalidades del tratamiento</h2>
          <ul>
            <li>Integrar y administrar el expediente clínico odontológico.</li>
            <li>Programar, confirmar y dar seguimiento a citas.</li>
            <li>
              Realizar diagnósticos, tratamientos, recetas y estudios
              comparativos.
            </li>
            <li>Contactar al paciente y enviar recordatorios.</li>
            <li>Cumplir obligaciones legales, sanitarias y administrativas.</li>
          </ul>
          <h2>Protección y conservación</h2>
          <p>
            Los datos se protegen mediante medidas administrativas y técnicas
            orientadas a evitar pérdida, alteración, acceso o uso no autorizado.
            Se conservarán durante el tiempo necesario para las finalidades
            clínicas y obligaciones legales.
          </p>
          <h2>Transferencias</h2>
          <p>
            La información sólo será compartida cuando resulte necesaria para la
            atención médica, por obligación legal o con autorización del
            titular.
          </p>
          <h2>Derechos del titular</h2>
          <p>
            El titular puede solicitar acceso, rectificación, cancelación u
            oposición al tratamiento de sus datos, así como revocar su
            consentimiento, mediante contacto directo con la clínica responsable
            de su expediente.
          </p>
          <h2>Cambios al aviso</h2>
          <p>
            Las modificaciones al presente aviso estarán disponibles dentro de
            SmileManager o serán comunicadas por la clínica.
          </p>
        </div>
      </article>
    </div>
  );
}
