# Mapeo React

| Templates legacy                                                                           | Página/componentes React                                                           | FUNC    |
| ------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------- | ------- |
| `sesiones/login.html`                                                                      | LoginPage, LoginForm                                                               | 001     |
| `Dentista/base.html`                                                                       | AppLayout, Navbar, Footer, ProtectedRoute                                          | 003     |
| `home/*`                                                                                   | DashboardPage, PrivacyPage                                                         | 004–005 |
| `pacientes/menuPacientes.html`                                                             | PatientsHubPage                                                                    | 006     |
| `registroPacientes`, `todosPacientes`, `buscar_pacientes`, `verPaciente`, `editarPaciente` | PatientCreate/List/Search/Detail/Edit pages, PatientForm                           | 007–012 |
| `historialMedico/menuHistorial.html`, selectors                                            | ClinicalRecordPage, PatientSelector                                                | 013     |
| `antecedentes.html`                                                                        | MedicalHistoryPage, BooleanQuestion                                                | 014     |
| `consultas`, `historial_consultas`, `receta`                                               | ConsultationCreate/History, PrescriptionPage                                       | 015–017 |
| `imagenes/*`                                                                               | ClinicalImagesHub/Upload/Search/History                                            | 018–022 |
| `odontograma.html`                                                                         | OdontogramPage + ToothChart/controls; portar JS sin perder estados                 | 023     |
| `before_after/*`                                                                           | ComparativeStudyPage (edición y visualización), previews y descarga PDF            | 024–026 |
| `consentimiento.html`                                                                      | ConsentPage                                                                        | 027     |
| `exportar_datos.html`                                                                      | ExportsPage                                                                        | 028–030 |
| `contactar_pacientes`, `contacto`                                                          | PatientContactPage                                                                 | 031     |
| `citas/*`                                                                                  | AppointmentsPage con calendario/lista/filtros, Create/Detail/Edit, AppointmentForm | 032–038 |
| `diagnosticos/*`                                                                           | DiagnosticsPage, DiagnosticResultPage, ImageViewer                                 | 039–040 |

Se reutilizan Bootstrap 5, Bootstrap Icons y OpenSeadragon. React se sirve bajo `/app/`, permitiendo comparación lado a lado. FUNC-041 continúa en `/admin/` y FUNC-042 es un comando sin interfaz, por lo que no tienen componente React.
