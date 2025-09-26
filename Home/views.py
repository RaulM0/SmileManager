from django.shortcuts import render
from Pacientes.models import Paciente
from Citas.models import Cita
from django.utils import timezone
from datetime import date
# Create your views here.

def home(request):
    numero_pacientes = Paciente.objects.filter(medico=request.user).count()
    hoy = date.today()  # obtiene la fecha actual
    citas_hoy = Cita.objects.filter(fecha=hoy, paciente__medico=request.user)
    proximas_citas = Cita.objects.filter(fecha__gt=hoy, paciente__medico=request.user)  # queryset
    return render(request, 'home/home.html', {
        'numero_pacientes': numero_pacientes,
        'citas_hoy': citas_hoy,
        'proximas_citas': proximas_citas
    })
