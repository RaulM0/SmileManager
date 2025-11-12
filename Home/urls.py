from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('aviso-privacidad/', views.aviso_privacidad, name='aviso_privacidad'),

]
