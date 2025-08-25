from django.urls import path
from . import views

urlpatterns = [
    path('', views.diagnosticos, name='diagnosticos'),
    path('resultados/<int:imagen_id>/', views.resultados, name='resultados'),
]