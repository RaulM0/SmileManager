from datetime import datetime
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from SmileManager import settings
from .models import Paciente, AntescedentesMedicos, Consulta, ImagenesClinicas
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
import pandas as pd
from django.core.mail import send_mail

# Create your views here.

def menuPacientes(request):
    return render(request, 'pacientes/menuPacientes.html')

def registrar_paciente(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre').upper()
        appat = request.POST.get('appat').upper()
        apmat = request.POST.get('apmat').upper()
        fecha_nac = request.POST.get('fecha_nacimiento')
        genero = request.POST.get('genero')
        tel = request.POST.get('telefono')
        email = request.POST.get('email').upper()
        
        if Paciente.objects.filter(telefono = tel).exists():
            messages.error(request, "El teléfono ya está registrado.")
            return render(request, 'pacientes/registroPacientes.html')
        
        # Crear al paciente
        Paciente.objects.create(
            nombre = nombre,
            appat = appat,
            apmat = apmat,
            fecha_nacimiento = fecha_nac,
            genero = genero,
            telefono = tel,
            email = email
        )
        messages.success(request, "Registro exitoso de paciente.")
        return redirect('/registroPacientes/registrar_pacientes/')
    return render(request, 'pacientes/registroPacientes.html')

def todos_los_pacientes(request):
    pacientes = Paciente.objects.all().order_by('appat')
    return render(request, 'pacientes/todosPacientes.html',{'pacientes': pacientes})

def buscar_pacientes(request):
    query = request.GET.get('q', '').strip()
    pacientes = Paciente.objects.all()

    if query:
        pacientes = pacientes.filter(
            Q(nombre__icontains=query) |
            Q(appat__icontains=query) |
            Q(apmat__icontains=query) |
            Q(telefono__icontains=query) |
            Q(email__icontains=query)
        )

    paginator = Paginator(pacientes, 10)  # 10 pacientes por página
    page = request.GET.get('page')
    pacientes_paginados = paginator.get_page(page)

    return render(request, 'pacientes/buscar_pacientes.html', {
        'pacientes': pacientes_paginados,
        'query': query
    })
    
def ver_paciente(request, id):
    paciente = Paciente.objects.filter(id=id).first()
    if not paciente:
        messages.error(request, 'Paciente no encontrado')
        return redirect('buscar_pacientes')
    else:
        edad = (datetime.today().date() - paciente.fecha_nacimiento).days // 365
        return render(request, 'pacientes/verPaciente.html', {'paciente': paciente, 'edad': edad})
    
def editar_paciente(request, id):
    paciente = Paciente.objects.filter(id=id).first()
    if not paciente:
        messages.error(request, 'Paciente no encontrado')
        return redirect('buscar_pacientes')

    if request.method == 'POST':
        paciente.nombre = request.POST.get('nombre').upper()
        paciente.appat = request.POST.get('appat').upper()
        paciente.apmat = request.POST.get('apmat').upper()
        paciente.fecha_nacimiento = request.POST.get('fecha_nacimiento')
        paciente.genero = request.POST.get('genero')
        paciente.telefono = request.POST.get('telefono')
        paciente.email = request.POST.get('email').upper()
        paciente.estatus = request.POST.get('estatus', 'Activo')
        
        if Paciente.objects.filter(telefono=paciente.telefono).exclude(id=id).exists():
            messages.error(request, "El teléfono ya está registrado.")
            return render(request, 'pacientes/editarPaciente.html', {'paciente': paciente})
        
        paciente.save()
        messages.success(request, "Paciente actualizado exitosamente.")
        return redirect('buscar_pacientes')

    return render(request, 'pacientes/editarPaciente.html', {'paciente': paciente})

#Aqui quiero que la eliminacion sea logica, que el campo estatus cambie a inactivo
def eliminar_paciente(request, id):
    paciente = Paciente.objects.filter(id=id).first()
    if not paciente:
        messages.error(request, 'Paciente no encontrado')
        return redirect('buscar_pacientes')

    if request.method == 'POST':
        paciente.estatus = 'I' 
        paciente.save()
        messages.success(request, "Paciente eliminado exitosamente.")
    
    return redirect('buscar_pacientes')

# Vistas del historial médico
def menu_historial(request):
    paciente_seleccionado = None
    paciente_id = request.GET.get('paciente_id')

    if paciente_id:
        try:
            paciente_seleccionado = Paciente.objects.get(id=paciente_id)
        except Paciente.DoesNotExist:
            paciente_seleccionado = None

    return render(request, 'historialMedico/menuHistorial.html', {
        'paciente_seleccionado': paciente_seleccionado
    })

def buscar_pacientes_ajax(request):
    term = request.GET.get('term', '')
    pacientes = Paciente.objects.filter(
        nombre__icontains=term
    )[:10]  # Limita resultados para mejor performance

    results = []
    for p in pacientes:
        results.append({
            'id': p.id,
            'text': f'{p.nombre} {p.appat} {p.apmat}'
        })
    return JsonResponse({'results': results})

def antecedentes(request, id):
    paciente = get_object_or_404(Paciente, id=id)
    antecedentes = AntescedentesMedicos.objects.filter(paciente=paciente).first()

    if request.method == 'POST':
        diabetes = request.POST.get('diabetes') == 'True'
        hipertension = request.POST.get('hipertension') == 'True'
        alergias = request.POST.get('alergias', '').upper()
        medicamentos = request.POST.get('medicamentos', '').upper()
        cirugias_previas = request.POST.get('cirugias_previas', '').upper()
        otros = request.POST.get('otros', '').upper()

        if not antecedentes:
            antecedentes = AntescedentesMedicos(paciente=paciente)
            created = True
        else:
            created = False

        antecedentes.diabetes = diabetes
        antecedentes.hipertension = hipertension
        antecedentes.alergias = alergias
        antecedentes.medicamentos = medicamentos
        antecedentes.cirugias_previas = cirugias_previas
        antecedentes.otros = otros
        antecedentes.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Antecedentes creados' if created else 'Antecedentes actualizados'
        })

    context = {
        'paciente': paciente,
        'antecedentes': antecedentes,
    }
    return render(request, 'historialMedico/antecedentes.html', context)

def consultas(request, id):
    paciente = Paciente.objects.filter(id=id).first()
    fecha = datetime.today().date().strftime('%Y-%m-%d')
    
    if request.method == 'POST':
        motivo_consulta = request.POST.get('motivo_consulta').upper()
        diagnostico = request.POST.get('diagnostico','Ninguno').upper()
        tratamiento = request.POST.get('tratamiento', 'Ninguno').upper()
        observaciones = request.POST.get('observaciones', 'Ninguna').upper()
        
        nueva_consulta = Consulta.objects.create(
            paciente=paciente,
            fecha_consulta=datetime.now(),
            motivo_consulta=motivo_consulta,
            diagnostico=diagnostico,
            tratamiento=tratamiento,
            observaciones=observaciones
        )
        
        messages.success(request, 'Consulta registrada exitosamente.')
        return redirect('receta', id=nueva_consulta.id)  # Redirige a la receta

    return render(request, 'historialMedico/consultas.html', {'paciente': paciente, 'fecha': fecha})


def receta(request, id):
    consulta = get_object_or_404(Consulta, id=id)
    return render(request, 'receta/receta.html', {'consulta': consulta})

def historial_consultas(request, id):
    paciente = get_object_or_404(Paciente, id=id)
    consultas = Consulta.objects.filter(paciente=paciente).order_by('-fecha_consulta')
    return render(request, 'historialMedico/historial_consultas.html',{'consultas': consultas, 'paciente': paciente})

# Vistas para imágenes clínicas
def imagenes_clinicas(request, id):
    paciente = get_object_or_404(Paciente, id=id)
    return render(request, 'imagenes/imagenes_clinicas.html', {'paciente': paciente})

def cargar_imagen(request, id):
    paciente = get_object_or_404(Paciente, id=id)
    consultas = Consulta.objects.filter(paciente=paciente).order_by('-fecha_consulta')

    if request.method == 'POST':
        consulta_id = request.POST.get('consulta_id')
        tipo_imagen = request.POST.get('tipo', '').strip().upper()
        descripcion = request.POST.get('descripcion', 'Ninguna').strip().upper()
        imagen = request.FILES.get('archivo')

        if not imagen:
            messages.error(request, "Por favor, sube una imagen.")
            return render(request, 'imagenes/cargarImagen.html', {'paciente': paciente, 'consultas': consultas})

        if not tipo_imagen or not descripcion:
            messages.error(request, "Todos los campos son obligatorios.")
            return render(request, 'imagenes/cargarImagen.html', {'paciente': paciente, 'consultas': consultas})

        if not consulta_id or not consulta_id.isdigit():
            messages.error(request, "Debes seleccionar una consulta válida.")
            return render(request, 'imagenes/cargarImagen.html', {'paciente': paciente, 'consultas': consultas})

        consulta = get_object_or_404(Consulta, id=consulta_id)

        ImagenesClinicas.objects.create(
            paciente=paciente,
            consulta=consulta,
            tipo_imagen=tipo_imagen,
            descripcion=descripcion,
            imagen=imagen
        )

        messages.success(request, "Imagen clínica cargada exitosamente.")
        return redirect('cargar_imagen', paciente.id)

    # GET: mostrar formulario
    return render(request, 'imagenes/cargarImagen.html', {'paciente': paciente, 'consultas': consultas})


def buscar_imagen(request, id):
    paciente = get_object_or_404(Paciente, id=id)
    consultas = Consulta.objects.filter(paciente=paciente).order_by('-fecha_consulta')
    imagenes = ImagenesClinicas.objects.filter(paciente=paciente)
    
    #Obtencion mediante get
    fecha = request.GET.get('fecha')
    consulta = request.GET.get('consulta_id')
    
    if fecha:
        imagenes = imagenes.filter(fecha_subida__date=fecha)
    
    if consulta:
        imagenes = imagenes.filter(consulta__id=consulta)
    
    return render(request, 'imagenes/buscar_imagen.html', {'paciente': paciente, 'consultas': consultas, 'imagenes': imagenes})

def eliminar_imagen(request, imagen_id):
    imagen = get_object_or_404(ImagenesClinicas, id=imagen_id)
    paciente_id = imagen.paciente.id  # Para redirigir después

    if request.method == 'POST':
        try:
            imagen.delete()
            messages.success(request, "Imagen clínica eliminada correctamente.")
        except Exception as e:
            messages.error(request, f"No se pudo eliminar la imagen: {str(e)}")
    else:
        messages.error(request, "Acción no permitida. La eliminación debe hacerse mediante un formulario POST.")

    return redirect('buscar_imagen', paciente_id)

def historial_imagenes(request, id):
    paciente = get_object_or_404(Paciente, id=id)
    imagenes = ImagenesClinicas.objects.filter(paciente=paciente).order_by('-fecha_subida')
    return render(request, 'imagenes/historial_imagenes.html',{
        'paciente': paciente,
        'imagenes': imagenes
    })

# Exportacion de datos a Excel
def exportar_datos(request):
    return render(request, 'pacientes/exportar_datos.html')

def exportar_pacientes(request):
    #Obtener los datos
    pacientes = Paciente.objects.all().values(
        'id','nombre','appat','apmat','fecha_nacimiento','genero','telefono','email','estatus'
    )
    #Convertir a Dataframe
    df = pd.DataFrame(list(pacientes))
    # Crear respuesta HTTP con Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=Pacientes.xlsx'
    
    #Guardar dataframe en el response como archivo Excel
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name= 'Pacientes', index=False)
        
    return response

def exportar_consultas(request):
    consultas = Consulta.objects.all().values(
        'paciente', 'fecha_consulta', 'motivo_consulta', 'diagnostico', 'tratamiento', 'observaciones'
    )

    df = pd.DataFrame(list(consultas))
    
    for col in df.select_dtypes(include=['datetimetz']):
        df[col] = df[col].dt.tz_localize(None)
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=Consultas.xlsx'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Consultas', index=False)
        
    return response
    
def exportar_imagenes(request):
    imagenes = ImagenesClinicas.objects.all().values(
        'paciente', 'consulta', 'tipo_imagen', 'descripcion', 'imagen', 'fecha_subida'
    )

    df = pd.DataFrame(list(imagenes))
    
    for col in df.select_dtypes(include=['datetimetz']):
        df[col] = df[col].dt.tz_localize(None)
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=ImagenesClinicas.xlsx'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='ImagenesClinicas', index=False)
        
    return response
    
# Vista para contactar pacientes
def contactar_pacientes(request):
    paciente_seleccionado = None
    paciente_id = request.GET.get('selectPaciente')

    if paciente_id:
        try:
            paciente_seleccionado = Paciente.objects.get(id=paciente_id)
        except Paciente.DoesNotExist:
            paciente_seleccionado = None

    return render(request, 'pacientes/contactar_pacientes.html', {
        'paciente_seleccionado': paciente_seleccionado
    })
    
def contacto(request, id):
    paciente = get_object_or_404(Paciente, id=id)
    return render(request, 'pacientes/contacto.html', {'paciente': paciente})

# Mandar un mensaje al paciente
def enviar_mensaje(request):
    if request.method == "POST":
        subject = request.POST.get("asunto")  # Asunto del correo
        message = request.POST.get("mensaje")  # Cuerpo del correo
        email_from = settings.EMAIL_HOST_USER # Correo de remitente

        recipient_list = [request.POST.get('email')] # Correo destinatario
        send_mail( subject, message, email_from, recipient_list )
        messages.success(request, "Correo enviado exitosamente.")
        #return render(request, "gracias.html") # formulario de agradecimiento, una vez enviado el correo 
    
    return render(request, "pacientes/contactar_pacientes.html") # Formulario de correo