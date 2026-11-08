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
from django.urls import path, include, re_path
from django.views.generic import RedirectView
from django.views.generic import TemplateView
from api import health



urlpatterns = [
    path('health', health.live),
    path('health/', health.live, name='health-live'),
    path('health/ready', health.ready),
    path('health/ready/', health.ready, name='health-ready'),
    path('', RedirectView.as_view(url='/app/', permanent=False), name='index'),
    path('api/v1/', include('api.urls')),
    re_path(r'^app(?:/.*)?$', TemplateView.as_view(template_name='index.html'), name='react-app'),
]
