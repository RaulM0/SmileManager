"""
URL configuration for SmileManager project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.views.generic import RedirectView



urlpatterns = [
    path('', RedirectView.as_view(url='/sesiones/login/', permanent=False), name='index'),

    path('admin/', admin.site.urls), # user: admin / password: 123
    path('home/', include('Home.urls')),
    path('registroPacientes/', include('Pacientes.urls')),
    path('menu_citas/', include('Citas.urls')),
    path('diagnosticos/', include('DiagnosticosIA.urls')),
    path('sesiones/', include('Sesiones.urls')),
]

#if settings.DEBUG:
#   urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)