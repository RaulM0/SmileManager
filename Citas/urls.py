from django.urls import path
from . import views

urlpatterns = [
    path('', views.menu_citas, name='menu_citas'),
    path('nueva_cita/', views.nueva_cita, name='nueva_cita'),
    path('registrar_cita/<int:id>/', views.registrar_cita, name='registrar_cita'),
    path('buscar_cita/', views.buscar_cita, name='buscar_cita'),
    path('editar_cita/<int:id>/', views.editar_cita, name='editar_cita'),
    path('citas_pendientes/', views.citas_pendientes, name='citas_pendientes'),
    path('citas_completadas/', views.citas_completadas, name='citas_completadas'),
    path('citas_canceladas/', views.citas_canceladas, name='citas_canceladas'),
    path('confirmar_asistencia/<int:id>/', views.confirmar_asistencia, name='confirmar_asistencia'),
    path('cancelar_cita/<int:id>/', views.anular_cita, name='cancelar_cita'),
    path('detalle_cita/<int:id>/', views.detalle_cita, name='detalle_cita'),
]