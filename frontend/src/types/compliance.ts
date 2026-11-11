export const noticeFields = [
  ['legal_name', 'Nombre legal o razón social del responsable'], ['address', 'Domicilio del responsable'],
  ['privacy_email', 'Correo para privacidad'], ['sensitive_data', 'Datos personales y datos sensibles'],
  ['purposes', 'Finalidades del tratamiento'], ['consent_purposes', 'Finalidades que requieren consentimiento'],
  ['arco_procedure', 'Procedimiento ARCO: canal, requisitos y plazos'], ['revocation_procedure', 'Procedimiento de revocación'],
  ['limitation_procedure', 'Opciones para limitar uso o divulgación'], ['transfers', 'Transferencias y proveedores'],
  ['retention', 'Conservación, bloqueo y eliminación'], ['changes_procedure', 'Cómo se comunicarán cambios'],
] as const;
export interface Notice { id: number; version: number; published_at: string; body: Record<string, string>; content_sha256: string }
export interface ConsentTemplate { id: number; kind: 'CLINICAL' | 'PRIVACY'; version: number; title: string; text: string; privacy_notice_id: number | null; content_sha256: string }
export interface ConsentEvidence { scan_status?: string; id: number; template: ConsentTemplate; signer_name: string; signer_role: string; signed_on: string; recorded_name: string; recorded_at: string; integrity: string; revoked_at: string | null; revocation_reason: string | null; superseded: boolean; file_url: string }
export interface ConsentWorkspace { templates: ConsentTemplate[]; records: ConsentEvidence[]; legacy: { fecha_aceptacion: string | null; texto: string; archivo_ine_url: string | null; pdf_generado: string | null } | null }
