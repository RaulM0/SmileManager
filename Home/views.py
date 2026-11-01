from django.shortcuts import render
from Pacientes.models import Paciente
from Citas.models import Cita
from api.policies import scoped
from django.utils import timezone
from datetime import date
# Create your views here.

def home(request):
    numero_pacientes = scoped(request.user, Paciente).count()
    hoy = date.today()  # obtiene la fecha actual
    citas_hoy = scoped(request.user, Cita).filter(fecha=hoy)
    proximas_citas = scoped(request.user, Cita).filter(fecha__gt=hoy)  # queryset
    return render(request, 'home/home.html', {
        'numero_pacientes': numero_pacientes,
        'citas_hoy': citas_hoy,
        'proximas_citas': proximas_citas
    })
    
def aviso_privacidad(request):
    return render(request, 'aviso_privacidad/aviso_privacidad.html')
