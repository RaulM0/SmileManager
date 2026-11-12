import type { FieldGuidance } from '../components/FieldLabelHelp';
import type { noticeFields } from '../types/compliance';

type NoticeKey = typeof noticeFields[number][0];
export const noticeGuidance: Record<NoticeKey, FieldGuidance> = {
  legal_name: { what: 'El nombre completo o la razón social de quien es responsable de los datos de la clínica.', purpose: 'Identifica al responsable en el aviso de privacidad.', example: 'Clínica Dental Ejemplo, S.A. de C.V.' },
  address: { what: 'El domicilio del responsable: calle, número, colonia, código postal, municipio y estado.', purpose: 'Permite localizar al responsable y conocer su domicilio de contacto.' },
  privacy_email: { what: 'Un correo que la clínica revise y utilice para atender solicitudes de privacidad.', purpose: 'Ofrece un canal de contacto para los titulares de los datos.', example: 'privacidad@clinica-ejemplo.com' },
  sensitive_data: { what: 'Las categorías de datos que realmente se recaban, distinguiendo datos de contacto y datos sensibles, como información de salud.', purpose: 'Explica al paciente qué información tratará la clínica. Describe categorías, sin incluir datos de pacientes reales.' },
  purposes: { what: 'Los usos concretos de los datos, como atención odontológica, expediente, citas y facturación.', purpose: 'Explica por qué se solicita la información y cómo se utilizará.' },
  consent_purposes: { what: 'Las finalidades para las que el procedimiento revisado de la clínica requiere consentimiento y cómo se solicitará.', purpose: 'Distingue los usos sujetos a autorización del titular. Debe coincidir con las plantillas y la revisión del responsable.' },
  arco_procedure: { what: 'Cómo solicitar acceso, rectificación, cancelación u oposición: canal, requisitos de identificación, pasos, plazos y forma de respuesta aprobados.', purpose: 'Indica al titular cómo ejercer sus derechos y cómo dará seguimiento la clínica.' },
  revocation_procedure: { what: 'El canal, los requisitos y los pasos para retirar un consentimiento, indicando las limitaciones que correspondan al procedimiento revisado.', purpose: 'Explica cómo solicitar y tramitar la revocación.' },
  limitation_procedure: { what: 'Las opciones y los canales disponibles para limitar el uso o la divulgación de los datos.', purpose: 'Permite conocer cómo solicitar restricciones sobre los usos de la información.' },
  transfers: { what: 'Los destinatarios o categorías de destinatarios, proveedores involucrados, datos compartidos y finalidades, conforme a lo revisado por la clínica.', purpose: 'Explica con quién se comparte información y por qué. Si no hay transferencias, indícalo según la revisión del responsable.' },
  retention: { what: 'Los criterios o plazos revisados para conservar, bloquear y eliminar cada categoría de información y sus excepciones.', purpose: 'Explica durante cuánto tiempo se resguardan los datos y qué sucede al terminar ese periodo.' },
  changes_procedure: { what: 'Dónde se publicarán las nuevas versiones del aviso y cómo se informará a los titulares.', purpose: 'Indica cómo consultar y conocer los cambios del aviso.', example: 'Las actualizaciones se publicarán en la sección de privacidad y estarán disponibles en recepción.' },
};

export const templateGuidance: Record<'kind' | 'title' | 'text', FieldGuidance> = {
  kind: { what: 'Selecciona Clínico para procedimientos de atención o Tratamiento de datos personales para la autorización de uso de datos.', purpose: 'Clasifica la plantilla para elegir el documento adecuado al registrar una evidencia.' },
  title: { what: 'Un nombre claro que identifique el procedimiento o la autorización.', purpose: 'Ayuda al personal a reconocer la plantilla al registrar documentos firmados.', example: 'Consentimiento para tratamiento odontológico' },
  text: { what: 'El contenido íntegro revisado y aprobado que aparecerá en el documento a firmar, incluyendo alcance, información al paciente y representación cuando corresponda.', purpose: 'Conserva una versión del texto con la que se cotejará el documento firmado. No incluyas datos de un paciente concreto.' },
};
