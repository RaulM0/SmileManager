from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views
from . import backoffice
from . import backoffice_clinical
from . import tenant_views
from . import tenant_patients
from . import tenant_appointments
from . import tenant_clinical_records
from . import tenant_consultations
from . import tenant_images
from . import tenant_ai
from . import tenant_consents
from . import tenant_reporting
from . import tenant_studies
from . import platform_clinics
from . import tenant_admin

router = DefaultRouter()
router.register('patients', views.PatientViewSet, basename='api-patient')
router.register('appointments', views.AppointmentViewSet, basename='api-appointment')
router.register('clinical-images', views.ClinicalImageViewSet, basename='api-clinical-image')


urlpatterns = [
    path('clinics/memberships/', tenant_views.MembershipList.as_view(), name='clinic-memberships'),
    path('clinics/context/', tenant_views.ValidateClinicContext.as_view(), name='clinic-context'),
    path('clinics/dashboard/', tenant_reporting.TenantDoctorDashboard.as_view(), name='tenant-doctor-dashboard'),
    path('clinics/admin/dashboard/', tenant_reporting.TenantAdminDashboard.as_view(), name='tenant-admin-dashboard'),
    path('clinics/admin/memberships/', tenant_admin.ClinicMembers.as_view(), name='tenant-admin-memberships'),
    path('clinics/admin/invitations/', tenant_admin.ClinicInvitations.as_view(), name='tenant-admin-invitations'),
    path('clinics/admin/audit/', tenant_admin.ClinicAudit.as_view(), name='tenant-admin-audit'),
    path('clinics/exports/<str:kind>.xlsx', tenant_reporting.TenantClinicalExport.as_view(), name='tenant-clinical-export'),
    path('clinics/patients/', tenant_patients.TenantPatientList.as_view(), name='tenant-patient-list'),
    path('clinics/patients/autocomplete/', tenant_patients.TenantPatientAutocomplete.as_view(), name='tenant-patient-autocomplete'),
    path('clinics/patients/<int:pk>/', tenant_patients.TenantPatientDetail.as_view(), name='tenant-patient-detail'),
    path('clinics/patients/<int:pk>/deactivate/', tenant_patients.TenantPatientDeactivate.as_view(), name='tenant-patient-deactivate'),
    path('clinics/patients/<int:patient_id>/medical-history/', tenant_clinical_records.TenantMedicalHistory.as_view(), name='tenant-medical-history'),
    path('clinics/patients/<int:patient_id>/odontogram/', tenant_clinical_records.TenantOdontogram.as_view(), name='tenant-odontogram'),
    path('clinics/patients/<int:patient_id>/consultations/', tenant_consultations.TenantConsultations.as_view(), name='tenant-consultations'),
    path('clinics/patients/<int:patient_id>/clinical-images/', tenant_images.TenantClinicalImages.as_view(), name='tenant-clinical-images'),
    path('clinics/patients/<int:patient_id>/consent/', tenant_consents.TenantConsent.as_view(), name='tenant-consent'),
    path('clinics/patients/<int:patient_id>/consent/<str:kind>/file/', tenant_consents.TenantConsentFile.as_view(), name='tenant-consent-file'),
    path('clinics/patients/<int:patient_id>/comparative-study/', tenant_studies.TenantComparativeStudy.as_view(), name='tenant-comparative-study'),
    path('clinics/patients/<int:patient_id>/comparative-study/pdf/', tenant_studies.TenantStudyPDF.as_view(), name='tenant-study-pdf'),
    path('clinics/patients/<int:patient_id>/comparative-study/media/<str:field>/', tenant_studies.TenantStudyImage.as_view(), name='tenant-study-image'),
    path('clinics/clinical-images/<int:image_id>/', tenant_images.TenantClinicalImageDetail.as_view(), name='tenant-clinical-image-detail'),
    path('clinics/diagnostics/', tenant_images.TenantDiagnostics.as_view(), name='tenant-diagnostics'),
    path('clinics/clinical-images/<int:image_id>/<str:kind>/file/', tenant_images.TenantClinicalImageFile.as_view(), name='tenant-clinical-image-file'),
    path('clinics/clinical-images/<int:image_id>/analyze/', tenant_ai.TenantAnalyzeImage.as_view(), name='tenant-analyze-image'),
    path('clinics/clinical-images/<int:image_id>/analysis-runs/', tenant_ai.TenantAnalysisRuns.as_view(), name='tenant-analysis-runs'),
    path('clinics/clinical-images/<int:image_id>/analysis-runs/<int:run_id>/file/', tenant_ai.TenantAnalysisRunFile.as_view(), name='tenant-analysis-run-file'),
    path('clinics/consultations/<int:consultation_id>/', tenant_consultations.TenantConsultationDetail.as_view(), name='tenant-consultation-detail'),
    path('clinics/appointments/', tenant_appointments.TenantAppointmentList.as_view(), name='tenant-appointment-list'),
    path('clinics/appointments/<int:pk>/', tenant_appointments.TenantAppointmentDetail.as_view(), name='tenant-appointment-detail'),
    path('clinics/appointments/<int:pk>/<str:operation>/', tenant_appointments.TenantAppointmentTransition.as_view(), name='tenant-appointment-transition'),
    path('clinics/memberships/<uuid:membership_id>/', tenant_views.MembershipDetail.as_view(), name='clinic-membership-detail'),
    path('clinics/invitations/', tenant_views.InvitationCreate.as_view(), name='clinic-invitation-create'),
    path('clinics/invitations/resolve/', tenant_views.InvitationResolve.as_view(), name='clinic-invitation-resolve'),
    path('clinics/invitations/register/', tenant_views.InvitationRegister.as_view(), name='clinic-invitation-register'),
    path('clinics/invitations/register/preview/', tenant_views.InvitationRegisterPreview.as_view(), name='clinic-invitation-register-preview'),
    path('clinics/invitations/preview/', tenant_views.InvitationPreview.as_view(), name='clinic-invitation-preview'),
    path('clinics/invitations/<uuid:invitation_id>/revoke/', tenant_views.InvitationRevoke.as_view(), name='clinic-invitation-revoke'),
    path('backoffice/patients/', backoffice_clinical.PatientList.as_view(), name='backoffice-patients'),
    path('backoffice/patients/<int:pk>/', backoffice_clinical.PatientDetail.as_view(), name='backoffice-patient'),
    path('backoffice/patients/<int:pk>/<str:section>/', backoffice_clinical.PatientSection.as_view(), name='backoffice-patient-section'),
    path('backoffice/appointments/', backoffice_clinical.AppointmentList.as_view(), name='backoffice-appointments'),
    path('backoffice/appointments/<int:pk>/', backoffice_clinical.AppointmentDetail.as_view(), name='backoffice-appointment'),
    path('backoffice/dashboard/', backoffice.Dashboard.as_view(), name='backoffice-dashboard'),
    path('backoffice/clinics/', platform_clinics.PlatformClinics.as_view(), name='platform-clinics'),
    path('backoffice/clinics/<uuid:clinic_id>/status/', platform_clinics.PlatformClinicStatus.as_view(), name='platform-clinic-status'),
    path('backoffice/clinics/<uuid:clinic_id>/initial-admin/', platform_clinics.PlatformInitialAdministrator.as_view(), name='platform-clinic-initial-admin'),
    path('backoffice/clinics/<uuid:clinic_id>/initial-admin/<uuid:invitation_id>/revoke/', platform_clinics.PlatformInitialAdministratorRevoke.as_view(), name='platform-clinic-initial-admin-revoke'),
    path('backoffice/users/', backoffice.Users.as_view(), name='backoffice-users'),
    path('backoffice/users/<int:pk>/', backoffice.UserDetail.as_view(), name='backoffice-user'),
    path('backoffice/users/<int:pk>/<str:operation>/', backoffice.UserActivation.as_view(), name='backoffice-user-action'),
    path('backoffice/audit/', backoffice.AuditList.as_view(), name='backoffice-audit'),
    path('backoffice/audit/<int:pk>/', backoffice.AuditDetail.as_view(), name='backoffice-audit-detail'),
    path('backoffice/ai-runs/', backoffice.Runs.as_view(), name='backoffice-ai-runs'),
    path('backoffice/ai-runs/<int:pk>/', backoffice.RunDetail.as_view(), name='backoffice-ai-run'),
    path('backoffice/system/', backoffice.System.as_view(), name='backoffice-system'),
    path('auth/session/', views.SessionView.as_view(), name='api-session'),
    path('auth/login/', views.LoginView.as_view(), name='api-login'),
    path('auth/refresh/', views.RefreshView.as_view(), name='api-refresh'),
    path('auth/logout/', views.LogoutView.as_view(), name='api-logout'),
    path('dashboard/', views.DashboardView.as_view(), name='api-dashboard'),
    path('patients/<int:patient_id>/medical-history/', views.MedicalHistoryView.as_view(), name='api-medical-history'),
    path('patients/<int:patient_id>/consultations/', views.ConsultationListCreateView.as_view(), name='api-consultations'),
    path('patients/<int:patient_id>/clinical-images/', views.ClinicalImageListCreateView.as_view(), name='api-clinical-images'),
    path('patients/<int:patient_id>/odontogram/', views.OdontogramView.as_view(), name='api-odontogram'),
    path('patients/<int:patient_id>/comparative-study/', views.ComparativeStudyView.as_view(), name='api-comparative-study'),
    path('patients/<int:patient_id>/comparative-study/pdf/', views.ComparativeStudyPdfView.as_view(), name='api-comparative-study-pdf'),
    path('patients/<int:patient_id>/comparative-study/media/<str:field>/', views.ComparativeStudyImageView.as_view(), name='api-comparative-study-image'),
    path('patients/<int:patient_id>/consent/', views.ConsentView.as_view(), name='api-consent'),
    path('patients/<int:patient_id>/consent/file/', views.ConsentFileView.as_view(), name='api-consent-file'),
    path('patients/<int:patient_id>/consent/pdf/', views.ConsentPdfView.as_view(), name='api-consent-pdf'),
    path('patients/<int:patient_id>/email/', views.PatientEmailView.as_view(), name='api-patient-email'),
    path('exports/patients.xlsx', views.PatientExportView.as_view(), name='api-export-patients'),
    path('exports/consultations.xlsx', views.ConsultationExportView.as_view(), name='api-export-consultations'),
    path('exports/clinical-images.xlsx', views.ClinicalImageExportView.as_view(), name='api-export-images'),
    path('diagnostics/', views.DiagnosticsView.as_view(), name='api-diagnostics'),
    path('consultations/<int:consultation_id>/', views.ConsultationDetailView.as_view(), name='api-consultation-detail'),
    path('clinical-images/<int:image_id>/analysis-runs/<int:run_id>/file/', views.AnalysisRunFileView.as_view(), name='api-analysis-run-file'),
    path('', include(router.urls)),
]
