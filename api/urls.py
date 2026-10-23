from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('patients', views.PatientViewSet, basename='api-patient')
router.register('appointments', views.AppointmentViewSet, basename='api-appointment')
router.register('clinical-images', views.ClinicalImageViewSet, basename='api-clinical-image')


urlpatterns = [
    path('auth/session/', views.SessionView.as_view(), name='api-session'),
    path('auth/login/', views.LoginView.as_view(), name='api-login'),
    path('auth/logout/', views.LogoutView.as_view(), name='api-logout'),
    path('dashboard/', views.DashboardView.as_view(), name='api-dashboard'),
    path('patients/<int:patient_id>/medical-history/', views.MedicalHistoryView.as_view(), name='api-medical-history'),
    path('patients/<int:patient_id>/consultations/', views.ConsultationListCreateView.as_view(), name='api-consultations'),
    path('patients/<int:patient_id>/clinical-images/', views.ClinicalImageListCreateView.as_view(), name='api-clinical-images'),
    path('patients/<int:patient_id>/odontogram/', views.OdontogramView.as_view(), name='api-odontogram'),
    path('patients/<int:patient_id>/comparative-study/', views.ComparativeStudyView.as_view(), name='api-comparative-study'),
    path('patients/<int:patient_id>/comparative-study/pdf/', views.ComparativeStudyPdfView.as_view(), name='api-comparative-study-pdf'),
    path('patients/<int:patient_id>/consent/', views.ConsentView.as_view(), name='api-consent'),
    path('patients/<int:patient_id>/email/', views.PatientEmailView.as_view(), name='api-patient-email'),
    path('exports/patients.xlsx', views.PatientExportView.as_view(), name='api-export-patients'),
    path('exports/consultations.xlsx', views.ConsultationExportView.as_view(), name='api-export-consultations'),
    path('exports/clinical-images.xlsx', views.ClinicalImageExportView.as_view(), name='api-export-images'),
    path('diagnostics/', views.DiagnosticsView.as_view(), name='api-diagnostics'),
    path('consultations/<int:consultation_id>/', views.ConsultationDetailView.as_view(), name='api-consultation-detail'),
    path('', include(router.urls)),
]
