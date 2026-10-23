# Mapeo API REST

Base: `/api/v1/`. Autenticación: sesión Django + CSRF. Todas las respuestas privadas requieren `IsAuthenticated`; querysets se limitan al médico.

| FUNC    | Método y endpoint                                                         | Entrada/salida principal         | Consumidor React          |
| ------- | ------------------------------------------------------------------------- | -------------------------------- | ------------------------- |
| 001     | POST `auth/login/`                                                        | username/password → user/profile | LoginPage                 |
| 002     | POST `auth/logout/`                                                       | 204                              | AppLayout                 |
| 003     | GET `auth/session/`                                                       | user/profile/authenticated       | AuthContext               |
| 004     | GET `dashboard/`                                                          | métricas y citas                 | DashboardPage             |
| 007–012 | GET/POST `patients/`; GET/PATCH `patients/{id}/`; POST `deactivate/`      | paciente y errores por campo     | Patient pages             |
| 013     | GET `patients/autocomplete/?term=`                                        | `{results:[id,text]}`            | PatientSelector           |
| 014     | GET/PUT `patients/{id}/medical-history/`                                  | indicadores/textos               | MedicalHistoryPage        |
| 015–017 | GET/POST `patients/{id}/consultations/`; GET `consultations/{id}/`        | consulta                         | Consultation/Prescription |
| 019–022 | GET/POST `patients/{id}/clinical-images/`; DELETE `clinical-images/{id}/` | multipart/imagen                 | Clinical image pages      |
| 023     | GET/PUT `patients/{id}/odontogram/`                                       | JSON denticiones/resumen         | OdontogramPage            |
| 024–026 | GET/PUT multipart `patients/{id}/comparative-study/`; GET `.../pdf/`      | estudio/PDF                      | Comparative pages         |
| 027     | GET/POST multipart `patients/{id}/consent/`                               | consentimiento                   | ConsentPage               |
| 028–030 | GET `exports/{patients                                                    | consultations                    | clinical-images}.xlsx`    | archivo | ExportsPage |
| 031     | POST `patients/{id}/email/`                                               | asunto/mensaje → confirmación    | PatientContactPage        |
| 032–038 | CRUD `appointments/`, actions `complete/`, `cancel/`                      | cita                             | Appointment pages         |
| 039     | GET `diagnostics/`                                                        | paginación + estadísticas        | DiagnosticsPage           |
| 040     | POST `clinical-images/{id}/analyze/`                                      | resultado + detecciones          | DiagnosticResultPage      |

Los contratos están implementados y fijados por la suite `api/tests/`. El login devuelve un token CSRF renovado porque Django lo rota al crear la sesión. Admin (FUNC-041) y recordatorios (FUNC-042) no necesitan endpoint REST: son interfaces operativas backend conservadas y probadas.
