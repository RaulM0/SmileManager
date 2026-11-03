from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views
from . import password_recovery
from . import backoffice
from . import backoffice_clinical

router = DefaultRouter()
router.register('patients', views.PatientViewSet, basename='api-patient')
router.register('appointments', views.AppointmentViewSet, basename='api-appointment')
router.register('clinical-images', views.ClinicalImageViewSet, basename='api-clinical-image')


urlpatterns = [
    path('backoffice/patients/', backoffice_clinical.PatientList.as_view(), name='backoffice-patients'),
    path('backoffice/patients/<int:pk>/', backoffice_clinical.PatientDetail.as_view(), name='backoffice-patient'),
    path('backoffice/patients/<int:pk>/records/<str:record>/', backoffice_clinical.PatientRecord.as_view(), name='backoffice-patient-record'),
    path('backoffice/patients/<int:pk>/<str:section>/', backoffice_clinical.PatientSection.as_view(), name='backoffice-patient-section'),
    path('backoffice/appointments/', backoffice_clinical.AppointmentList.as_view(), name='backoffice-appointments'),
    path('backoffice/appointments/<int:pk>/', backoffice_clinical.AppointmentDetail.as_view(), name='backoffice-appointment'),
    path('backoffice/appointments/<int:pk>/<str:operation>/', backoffice_clinical.AppointmentTransition.as_view(), name='backoffice-appointment-transition'),
    path('backoffice/dashboard/', backoffice.Dashboard.as_view(), name='backoffice-dashboard'),
    path('backoffice/users/', backoffice.Users.as_view(), name='backoffice-users'),
    path('backoffice/users/create/', backoffice.CreateUser.as_view(), name='backoffice-user-create'),
    path('backoffice/users/<int:pk>/', backoffice.UserDetail.as_view(), name='backoffice-user'),
    path('backoffice/users/<int:pk>/<str:operation>/', backoffice.UserActivation.as_view(), name='backoffice-user-action'),
    path('backoffice/audit/', backoffice.AuditList.as_view(), name='backoffice-audit'),
    path('backoffice/audit/<int:pk>/', backoffice.AuditDetail.as_view(), name='backoffice-audit-detail'),
    path('backoffice/ai-runs/', backoffice.Runs.as_view(), name='backoffice-ai-runs'),
    path('backoffice/ai-runs/<int:pk>/', backoffice.RunDetail.as_view(), name='backoffice-ai-run'),
    path('backoffice/system/', backoffice.System.as_view(), name='backoffice-system'),
    path('auth/session/', views.SessionView.as_view(), name='api-session'),
    path('auth/login/', views.LoginView.as_view(), name='api-login'),
    path('auth/password-reset/request/', password_recovery.PasswordResetRequest.as_view(), name='api-password-reset-request'),
    path('auth/password-reset/confirm/', password_recovery.PasswordResetConfirm.as_view(), name='api-password-reset-confirm'),
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
