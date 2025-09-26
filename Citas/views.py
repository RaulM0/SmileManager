from django.shortcuts import get_object_or_404, render, redirect
from Pacientes.models import Paciente
from .models import Cita
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from django.core.paginator import Paginator
from django.db.models import Q



# Create your views here.
def menu_citas(request):
    citas = Cita.objects.filter(paciente__medico=request.user).select_related('paciente')
    current_date = timezone.now()
    
    return render(request, 'citas/menu_citas.html', {
        'citas': citas,
        'current_date': current_date
    })

def nueva_cita(request):
    return render(request, 'citas/nueva_cita.html')

def registrar_cita(request, id):
    paciente = get_object_or_404(Paciente, id=id, medico=request.user)

    if request.method == 'POST':
        fecha = request.POST.get('fecha')
        hora = request.POST.get('hora')
        motivo = request.POST.get('motivo', 'Ninguno')
        estatus = request.POST.get('estatus', 'P')
        observaciones = request.POST.get('observaciones', 'Ninguna')

        # Validaciones
        if not fecha or not hora:
            messages.error(request, "La fecha y hora son obligatorias.")
            return redirect('registrar_cita', id=id)

        try:
            fecha_cita = datetime.strptime(fecha, "%Y-%m-%d").date()
            hora_cita = datetime.strptime(hora, "%H:%M").time()
        except ValueError:
            messages.error(request, "Formato de fecha u hora inválido.")
            return redirect('registrar_cita', id=id)

        # No permitir fechas pasadas
        if fecha_cita < timezone.now().date():
            messages.error(request, "No puedes registrar una cita en una fecha pasada.")
            return redirect('registrar_cita', id=id)

        # Validar hora
        if hora_cita < datetime.strptime("08:00", "%H:%M").time() or hora_cita > datetime.strptime("20:00", "%H:%M").time():
            messages.error(request, "La hora debe estar entre las 08:00 y las 20:00.")
            return redirect('registrar_cita', id=id)

        # Guardar cita
        Cita.objects.create(
            paciente=paciente,
            fecha=fecha,
            hora=hora,
            motivo=motivo,
            estatus=estatus,
            observaciones=observaciones
        )
        messages.success(request, "Cita registrada correctamente.")
        return redirect('registrar_cita', id=id)

    return render(request, 'citas/registrar_cita.html', {'paciente': paciente})

def buscar_cita(request):
    query = request.GET.get('buscador', '').strip()
    citas = Cita.objects.filter(paciente__medico=request.user)

    if query:
        citas = citas.filter(
            Q(paciente__nombre__icontains=query) |
            Q(id__icontains=query) |
            Q(paciente__appat__icontains=query) |
            Q(paciente__telefono__icontains=query)
        )
    return render(request, 'citas/buscar_cita.html', {'citas': citas,})

def editar_cita(request, id):
    cita = get_object_or_404(Cita, id=id, paciente__medico=request.user)
    if request.method == 'POST':
        fecha = request.POST.get('fecha')
        hora = request.POST.get('hora')
        motivo = request.POST.get('motivo', 'Ninguno')
        estatus = request.POST.get('estatus', 'P')
        observaciones = request.POST.get('observaciones', 'Ninguna')
        # Validaciones
        if not fecha or not hora:
            messages.error(request, "La fecha y hora son obligatorias.")
            return redirect('editar_cita', id=id)   
        try:
            fecha_cita = datetime.strptime(fecha, "%Y-%m-%d").date()
            hora_cita = datetime.strptime(hora, "%H:%M").time()
        except ValueError:
            messages.error(request, "Formato de fecha u hora inválido.")
            return redirect('registrar_cita', id=id)
        
        # No permitir fechas pasadas
        if fecha_cita < timezone.now().date():
            messages.error(request, "No puedes editar una cita a una fecha pasada.")
            return redirect('editar_cita', id=id)
        # Validar hora
        if hora_cita < datetime.strptime("08:00", "%H:%M").time() or hora_cita > datetime.strptime("20:00", "%H:%M").time():
            messages.error(request, "La hora debe estar entre las 08:00 y las 20:00.")
            return redirect('editar_cita', id=id)
        # Actualizar cita
        cita.fecha = fecha
        cita.hora = hora
        cita.motivo = motivo
        cita.estatus = estatus
        cita.observaciones = observaciones
        cita.save()
        messages.success(request, "Cita actualizada correctamente.")
        
    estatus_options = {
    'P': 'selected' if cita.estatus == 'P' else '',
    'C': 'selected' if cita.estatus == 'C' else '',
    'A': 'selected' if cita.estatus == 'A' else '',
    }
    return render(request, 'citas/editar_cita.html', {'cita': cita, 'estatus_options': estatus_options})

def citas_pendientes(request):
    citas_pendientes = Cita.objects.filter(estatus='P', paciente__medico=request.user).order_by('fecha', 'hora')
    return render(request, 'citas/citas_pendientes.html', {'citas_pendientes': citas_pendientes})

def citas_completadas(request):
    citas_completadas = Cita.objects.filter(estatus = 'C', paciente__medico=request.user).order_by('fecha','hora')
    return render(request, 'citas/citas_completadas.html', {'citas_completadas':citas_completadas})

def citas_canceladas(request):
    citas_canceladas = Cita.objects.filter(estatus = 'A', paciente__medico=request.user).order_by('fecha','hora')
    return render(request, 'citas/citas_canceladas.html', {'citas_canceladas':citas_canceladas})

def confirmar_asistencia(request, id):
    cita = get_object_or_404(Cita, id=id, paciente__medico=request.user)
    cita.estatus = 'C'
    cita.save()
    messages.success(request, "Cita marcada como completada.")
    return redirect('citas_pendientes')

def anular_cita(request, id):
    cita = get_object_or_404(Cita, id=id, paciente__medico=request.user)
    cita.estatus = 'A'
    cita.save()
    messages.success(request, "Cita anulada correctamente.")
    return redirect('citas_pendientes')

def detalle_cita(request, id):
    cita = get_object_or_404(Cita, id=id, paciente__medico=request.user)
    return render(request, 'citas/detalles_cita.html', {'cita': cita})