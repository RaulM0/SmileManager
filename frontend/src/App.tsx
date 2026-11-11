import { lazy, Suspense } from "react";
import type { ReactNode } from "react";
import { createBrowserRouter, createRoutesFromElements, Navigate, Route, RouterProvider } from "react-router-dom";
import ClinicWorkspace from "./layouts/ClinicWorkspace";
import ProtectedRoute from "./routes/ProtectedRoute";
import LoginPage from "./pages/LoginPage";
import { ForgotPasswordPage, ResetPasswordPage } from "./pages/PasswordRecovery";
import InvitationPage from "./pages/InvitationPage";
import InvitationRegisterPage from "./pages/InvitationRegisterPage";
import DashboardPage from "./pages/DashboardPage";
import PrivacyPage from "./pages/PrivacyPage";
import SecurityPage from './pages/SecurityPage';
import CompliancePage from './pages/CompliancePage';
import PatientsHubPage from "./pages/patients/PatientsHubPage";
import PatientListPage from "./pages/patients/PatientListPage";
import PatientCreatePage from "./pages/patients/PatientCreatePage";
import PatientEditPage from "./pages/patients/PatientEditPage";
import PatientDetailPage from "./pages/patients/PatientDetailPage";
import ClinicalRecordSelectPage from "./pages/clinical/ClinicalRecordSelectPage";
import ClinicalRecordPage from "./pages/clinical/ClinicalRecordPage";
import MedicalHistoryPage from "./pages/clinical/MedicalHistoryPage";
import ConsultationCreatePage from "./pages/clinical/ConsultationCreatePage";
import ConsultationHistoryPage from "./pages/clinical/ConsultationHistoryPage";
import PrescriptionPage from "./pages/clinical/PrescriptionPage";
import AppointmentsPage from "./pages/appointments/AppointmentsPage";
import AppointmentCreatePage from "./pages/appointments/AppointmentCreatePage";
import AppointmentEditPage from "./pages/appointments/AppointmentEditPage";
import AppointmentDetailPage from "./pages/appointments/AppointmentDetailPage";
import ClinicalImagesHubPage from "./pages/images/ClinicalImagesHubPage";
import ClinicalImageUploadPage from "./pages/images/ClinicalImageUploadPage";
import ClinicalImageListPage from "./pages/images/ClinicalImageListPage";
import OdontogramPage from "./pages/clinical/OdontogramPage";
import ComparativeStudyPage from "./pages/clinical/ComparativeStudyPage";
import ConsentPage from "./pages/clinical/ConsentPage";
import ExportsPage from "./pages/exports/ExportsPage";
import PatientContactPage from "./pages/patients/PatientContactPage";
import DiagnosticsPage from "./pages/diagnostics/DiagnosticsPage";
import { BackofficeLayout, BackofficeDashboard, BackofficeUsers, BackofficeUser, BackofficeAudit, BackofficeRuns, BackofficeRun, BackofficeSystem } from "./pages/backoffice/Backoffice";
import { BackofficePatients, BackofficePatient, BackofficePatientEdit, BackofficePatientSection, BackofficeAppointments, BackofficeAppointment } from "./pages/backoffice/BackofficeClinical";
import { BackofficeUserCreate } from "./pages/backoffice/BackofficeUserCreate";
import PlatformClinicsPage from "./pages/backoffice/PlatformClinicsPage";
import { useAuth } from "./context/AuthContext";

const DiagnosticResultPage = lazy(
  () => import("./pages/diagnostics/DiagnosticResultPage"),
);
const DesignSystemLab = import.meta.env.DEV ? lazy(() => import("./design-system/DesignSystemLab")) : null;

function RouteLoading() {
  return (
    <div className="page-loader" role="status" aria-label="Cargando pantalla">
      <div className="workspace-loader-spinner" />
    </div>
  );
}

function GlobalAIFeatureRoute({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  return user?.ai_globally_enabled ? children : <Navigate to="/backoffice" replace />;
}

const router = createBrowserRouter(createRoutesFromElements(
    <>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/privacy/:clinicSlug" element={<PrivacyPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
      <Route path="/invitations/register" element={<InvitationRegisterPage />} />
      <Route element={<ProtectedRoute />}>
        <Route path="security" element={<SecurityPage />} />
        <Route path="compliance" element={<CompliancePage />} />
        <Route path="privacy" element={<PrivacyPage />} />
        <Route path="invitations/accept" element={<InvitationPage />} />
        <Route path="backoffice" element={<BackofficeLayout />}>
          <Route index element={<BackofficeDashboard />} />
          <Route path="users" element={<BackofficeUsers />} />
          <Route path="users/new" element={<BackofficeUserCreate />} />
          <Route path="users/:id" element={<BackofficeUser />} />
          <Route path="patients" element={<BackofficePatients />} />
          <Route path="patients/:id" element={<BackofficePatient />} />
          <Route path="patients/:id/edit" element={<BackofficePatientEdit />} />
          <Route path="patients/:id/edit-history" element={<MedicalHistoryPage administrative />} />
          <Route path="patients/:id/edit-odontogram" element={<OdontogramPage administrative />} />
          <Route path="patients/:id/:section" element={<BackofficePatientSection />} />
          <Route path="appointments" element={<BackofficeAppointments />} />
          <Route path="appointments/:id" element={<BackofficeAppointment />} />
          <Route path="audit" element={<BackofficeAudit />} />
          <Route path="ai" element={<GlobalAIFeatureRoute><BackofficeRuns /></GlobalAIFeatureRoute>} />
          <Route path="ai/:id" element={<GlobalAIFeatureRoute><BackofficeRun /></GlobalAIFeatureRoute>} />
          <Route path="system" element={<BackofficeSystem />} />
          <Route path="clinics" element={<PlatformClinicsPage />} />
        </Route>
        <Route element={<ClinicWorkspace />}>
          <Route index element={<DashboardPage />} />
          {DesignSystemLab && <Route path="design-system" element={<Suspense fallback={<RouteLoading />}><DesignSystemLab /></Suspense>} />}
          <Route path="patients" element={<PatientsHubPage />} />
          <Route path="patients/list" element={<PatientListPage />} />
          <Route
            path="patients/search"
            element={<PatientListPage searchable />}
          />
          <Route path="patients/new" element={<PatientCreatePage />} />
          <Route path="patients/contact" element={<PatientContactPage />} />
          <Route path="patients/:id" element={<PatientDetailPage />} />
          <Route path="patients/:id/edit" element={<PatientEditPage />} />
          <Route
            path="clinical-record"
            element={<ClinicalRecordSelectPage />}
          />
          <Route path="patients/:id/record" element={<ClinicalRecordPage />} />
          <Route
            path="patients/:id/medical-history"
            element={<MedicalHistoryPage />}
          />
          <Route
            path="patients/:id/consultations/new"
            element={<ConsultationCreatePage />}
          />
          <Route
            path="patients/:id/consultations"
            element={<ConsultationHistoryPage />}
          />
          <Route
            path="consultations/:id/prescription"
            element={<PrescriptionPage />}
          />
          <Route
            path="patients/:id/images"
            element={<ClinicalImagesHubPage />}
          />
          <Route
            path="patients/:id/images/upload"
            element={<ClinicalImageUploadPage />}
          />
          <Route
            path="patients/:id/images/search"
            element={<ClinicalImageListPage searchable />}
          />
          <Route
            path="patients/:id/images/history"
            element={<ClinicalImageListPage />}
          />
          <Route path="patients/:id/odontogram" element={<OdontogramPage />} />
          <Route
            path="patients/:id/comparative-study"
            element={<ComparativeStudyPage />}
          />
          <Route path="patients/:id/consent" element={<ConsentPage />} />
          <Route path="exports" element={<ExportsPage />} />
          <Route path="diagnostics" element={<DiagnosticsPage />} />
          <Route
            path="diagnostics/:id"
            element={
              <Suspense fallback={<RouteLoading />}>
                <DiagnosticResultPage />
              </Suspense>
            }
          />
          <Route path="appointments" element={<AppointmentsPage />} />
          <Route path="appointments/new" element={<AppointmentCreatePage />} />
          <Route path="appointments/:id" element={<AppointmentDetailPage />} />
          <Route
            path="appointments/:id/edit"
            element={<AppointmentEditPage />}
          />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </>
), { basename: import.meta.env.PROD ? "/app" : undefined });

export default function App() {
  return <RouterProvider router={router} />;
}
