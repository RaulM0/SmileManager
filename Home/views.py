from django.shortcuts import render
from Pacientes.models import Paciente
from Citas.models import Cita
from django.utils import timezone
from datetime import date
# Create your views here.

'''
def home(request):
    numero_pacientes = Paciente.objects.count()
    citas_hoy = Cita.objects.filter(fecha__date=timezone.now().date()).count()
    return render(request, 'home/home.html', {'numero_pacientes': numero_pacientes, 'citas_hoy': citas_hoy})


'''

def home(request):
    numero_pacientes = Paciente.objects.count()
    hoy = date.today()  # obtiene la fecha actual
    citas_hoy = Cita.objects.filter(fecha=hoy)
    proximas_citas = Cita.objects.filter(fecha__gt=hoy)  # queryset
    return render(request, 'home/home.html', {
        'numero_pacientes': numero_pacientes,
        'citas_hoy': citas_hoy,
        'proximas_citas': proximas_citas
    })
