---
generated: true
source: "api/views.py"
aliases: ["api/views.py"]
tags: [mapa, archivo]
---
# views.py

Módulo: [[docs/mapa/API y seguridad]]. Inicio: [[docs/mapa/Inicio]].

## Archivo real

Ruta desde la raíz: `api/views.py`.

[Abrir archivo del proyecto](../../../api/views.py)

El enlace apunta al código original. Según el tipo de archivo, Obsidian lo abrirá o permitirá abrirlo con la aplicación predeterminada. Esta nota es un índice; leer el archivo real antes de modificarlo.

## Símbolos principales

- `LoginInputSerializer` — línea 62.
- `_auth_origin_allowed` — línea 71.
- `_refresh_user` — línea 79.
- `_set_refresh_cookie` — línea 91.
- `SessionView` — línea 101.
- `LoginView` — línea 127.
- `RefreshView` — línea 173.
- `LogoutView` — línea 204.
- `DashboardView` — línea 229.
- `PatientPagination` — línea 244.
- `ClinicalPagination` — línea 248.
- `PatientViewSet` — línea 257.
- `OwnedPatientMixin` — línea 301.
- `MedicalHistoryView` — línea 306.
- `ConsultationListCreateView` — línea 323.
- `ConsultationDetailView` — línea 342.
- `AppointmentViewSet` — línea 352.
- `ClinicalImageListCreateView` — línea 398.
- `ClinicalImageViewSet` — línea 427.
- `AnalysisRunFileView` — línea 501.
- `OdontogramView` — línea 513.
- `ComparativeStudyView` — línea 538.
- `ComparativeStudyPdfView` — línea 550.
- `ComparativeStudyImageView` — línea 558.
- `ConsentView` — línea 571.
- `ConsentFileView` — línea 589.
- `ConsentPdfView` — línea 598.
- `PatientEmailInputSerializer` — línea 606.
- `PatientEmailView` — línea 610.
- `PatientExportView` — línea 617.
- `ConsultationExportView` — línea 620.
- `ClinicalImageExportView` — línea 623.
- `DiagnosticsView` — línea 627.

## Dependencias internas

- [[docs/mapa/archivos/Citas_2Fmodels.py|Citas/models.py]]
- [[docs/mapa/archivos/DiagnosticosIA_2Fmodels.py|DiagnosticosIA/models.py]]
- [[docs/mapa/archivos/DiagnosticosIA_2Fruns.py|DiagnosticosIA/runs.py]]
- [[docs/mapa/archivos/DiagnosticosIA_2Fservices.py|DiagnosticosIA/services.py]]
- [[docs/mapa/archivos/Pacientes_2FPDF.py|Pacientes/PDF.py]]
- [[docs/mapa/archivos/Pacientes_2Fmodels.py|Pacientes/models.py]]
- [[docs/mapa/archivos/Usuarios_2Fmodels.py|Usuarios/models.py]]
- [[docs/mapa/archivos/api_2Fauthentication.py|api/authentication.py]]
- [[docs/mapa/archivos/api_2Fpolicies.py|api/policies.py]]
- [[docs/mapa/archivos/api_2Fserializers.py|api/serializers.py]]
- [[docs/mapa/archivos/api_2Fservices_2Fappointments.py|api/services/appointments.py]]
- [[docs/mapa/archivos/api_2Fservices_2Fclinical_records.py|api/services/clinical_records.py]]
- [[docs/mapa/archivos/api_2Fservices_2Femails.py|api/services/emails.py]]
- [[docs/mapa/archivos/api_2Fservices_2Fexports.py|api/services/exports.py]]
- [[docs/mapa/archivos/api_2Fservices_2Fmfa.py|api/services/mfa.py]]
- [[docs/mapa/archivos/api_2Fservices_2Fpatients.py|api/services/patients.py]]
- [[docs/mapa/archivos/api_2Fthrottles.py|api/throttles.py]]
- [[docs/mapa/archivos/api_2Fupload_policy.py|api/upload_policy.py]]

Este índice resuelve imports Python y referencias relativas JS/TS; no ejecuta módulos ni representa todas las dependencias dinámicas.
