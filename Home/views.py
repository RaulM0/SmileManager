from django.shortcuts import render
from Pacientes.models import Paciente

# Create your views here.

def home(request):
    numero_pacientes = Paciente.objects.count()
    return render(request, 'home/home.html', {'numero_pacientes': numero_pacientes})