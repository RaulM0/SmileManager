from datetime import datetime
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from SmileManager import settings
from .models import Paciente, AntescedentesMedicos, Consulta, ImagenesClinicas, Odontograma
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
import pandas as pd
from django.core.mail import send_mail
from django.db.models.functions import Concat
from django.db.models import Value
import json

from django.views.decorators.csrf import csrf_exempt


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
            email = email,
            medico = request.user
        )
        messages.success(request, "Registro exitoso de paciente.")
        return redirect('/registroPacientes/registrar_pacientes/')
    return render(request, 'pacientes/registroPacientes.html')

def todos_los_pacientes(request):
    pacientes = Paciente.objects.filter(medico=request.user).order_by('appat')
    return render(request, 'pacientes/todosPacientes.html',{'pacientes': pacientes})

def buscar_pacientes(request):
    query = request.GET.get('q', '').strip()
    pacientes = Paciente.objects.filter(medico=request.user).order_by('appat')

    if query:
        pacientes = pacientes.annotate(
            nombre_completo=Concat('nombre', Value(' '), 'appat', Value(' '), 'apmat')
        ).filter(
            Q(nombre__icontains=query) |
            Q(appat__icontains=query) |
            Q(apmat__icontains=query) |
            Q(telefono__icontains=query) |
            Q(email__icontains=query) |
            Q(nombre_completo__icontains=query)
        )

    paginator = Paginator(pacientes, 10)
    page = request.GET.get('page')
    pacientes_paginados = paginator.get_page(page)

    return render(request, 'pacientes/buscar_pacientes.html', {
        'pacientes': pacientes_paginados,
        'query': query
    })
    
def ver_paciente(request, id):
    paciente = Paciente.objects.filter(id=id, medico= request.user).first()
    if not paciente:
        messages.error(request, 'Paciente no encontrado')
        return redirect('buscar_pacientes')
    else:
        edad = (datetime.today().date() - paciente.fecha_nacimiento).days // 365
        return render(request, 'pacientes/verPaciente.html', {'paciente': paciente, 'edad': edad})
    
def editar_paciente(request, id):
    paciente = Paciente.objects.filter(id=id, medico=request.user).first()
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
    paciente = Paciente.objects.filter(id=id, medico = request.user).first()
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
            paciente_seleccionado = Paciente.objects.get(id=paciente_id, medico=request.user)
        except Paciente.DoesNotExist:
            paciente_seleccionado = None

    return render(request, 'historialMedico/menuHistorial.html', {
        'paciente_seleccionado': paciente_seleccionado
    })

def buscar_pacientes_ajax(request):
    term = request.GET.get('term', '')
    pacientes = Paciente.objects.filter(
        medico=request.user,
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
    paciente = get_object_or_404(Paciente, id=id, medico=request.user)
    
    antecedentes, created = AntescedentesMedicos.objects.get_or_create(id_paciente=paciente)
    
    if request.method == 'POST':
        form_data = request.POST

        # Campos booleanos
        bool_fields = [
            'tratamiento_medico', 'problemas_cardiacos', 'problemas_coagulacion',
            'epilepsia', 'gastritis', 'hipertension', 'anemia', 'embarazo',
            'alergia_medicamentos', 'alergia_especifica', 'discapacidad', 'fuma',
            'respiracion_bucal', 'morder_unas', 'chupar_dedo', 'rechinar_dientes',
            'sobremordida_vertical', 'sobremordida_horizontal', 'mordida_cruzada',
            'mordida_abierta', 'desgaste', 'problemas_atm', 'consumo_citricos',
            'sangrado_encias'
        ]

        for field in bool_fields:
            setattr(antecedentes, field, form_data.get(field) == 'True')

        # Campos de texto
        antecedentes.alergias = form_data.get('alergias_txt', '')
        antecedentes.medicamentos = form_data.get('medicamentos', '')
        antecedentes.cirugias_previas = form_data.get('cirugias_previas', '')
        antecedentes.otros = form_data.get('otros', '')

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
        

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import datetime
from .models import Paciente, Consulta


def consultas(request, id):
    paciente = get_object_or_404(Paciente, id=id, medico=request.user)
    fecha = datetime.today().date().strftime('%Y-%m-%d')
    
    if request.method == 'POST':
        motivo_consulta = request.POST.get('motivo_consulta', '').upper()
        diagnostico = request.POST.get('diagnostico', 'Ninguno').upper()
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
    paciente = get_object_or_404(Paciente, id=id, medico=request.user)
    consultas = Consulta.objects.filter(paciente=paciente).order_by('-fecha_consulta')
    return render(request, 'historialMedico/historial_consultas.html',{'consultas': consultas, 'paciente': paciente})

# Vistas para imágenes clínicas
def imagenes_clinicas(request, id):
    paciente = get_object_or_404(Paciente, id=id)
    return render(request, 'imagenes/imagenes_clinicas.html', {'paciente': paciente})

def cargar_imagen(request, id):
    paciente = get_object_or_404(Paciente, id=id, medico=request.user)
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
    paciente = get_object_or_404(Paciente, id=id, medico=request.user)
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
    paciente = get_object_or_404(Paciente, id=id, medico=request.user)
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
    pacientes = Paciente.objects.filter(medico=request.user).values(
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

from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
import pandas as pd
from .models import Consulta

def exportar_consultas(request):
    # Solo consultas de pacientes del médico logueado
    consultas = Consulta.objects.filter(
        paciente__medico=request.user
    ).values(
        'paciente__nombre', 'paciente__appat', 'paciente__apmat',
        'fecha_consulta', 'motivo_consulta', 'diagnostico', 
        'tratamiento', 'observaciones'
    )

    df = pd.DataFrame(list(consultas))
    
    # Quitar la zona horaria si existe
    for col in df.select_dtypes(include=['datetimetz']):
        df[col] = df[col].dt.tz_localize(None)
    
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=Consultas.xlsx'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Consultas', index=False)
        
    return response

    
def exportar_imagenes(request):
    imagenes = ImagenesClinicas.objects.filter(
            paciente__medico=request.user
        ).values(
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


def odontograma(request, id):
    paciente = get_object_or_404(Paciente, id=id, medico=request.user)
    
    # Tomamos el odontograma más reciente del paciente
    odontograma_obj = (
        paciente.odontogramas.order_by('-created').first()
    )
    
    if odontograma_obj:
        odontograma_data = json.dumps({
            'dientes_permanentes': odontograma_obj.dientes_permanentes,
            'dientes_deciduos': odontograma_obj.dientes_deciduos,
            'resumen': odontograma_obj.resumen_clinico
        })
    else:
        odontograma_data = json.dumps({})  # vacío si no existe
    
    context = {
        'paciente': paciente,
        'odontograma_data': odontograma_data
    }
    
    return render(request, 'odontograma/odontograma.html', context)



@csrf_exempt
def guardar_odontograma(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id, medico=request.user)

    if request.method == 'POST':
        data = json.loads(request.body)  # JSON enviado desde el frontend
        dientes_permanentes = data.get('denticion_permanente', {})
        dientes_deciduos = data.get('denticion_decidua', {})
        resumen_clinico = data.get('resumen', {})

        # Buscamos si ya existe un odontograma para este paciente
        odontograma, created = Odontograma.objects.get_or_create(
            paciente=paciente,
            defaults={
                'dientes_permanentes': dientes_permanentes,
                'dientes_deciduos': dientes_deciduos,
                'resumen_clinico': resumen_clinico
            }
        )

        if not created:
            # Si ya existe, hacemos update
            odontograma.dientes_permanentes = dientes_permanentes
            odontograma.dientes_deciduos = dientes_deciduos
            odontograma.resumen_clinico = resumen_clinico
            odontograma.save()

        return JsonResponse({
            'status': 'ok',
            'mensaje': 'Odontograma guardado' if created else 'Odontograma actualizado',
            'id': odontograma.id
        })

    return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'}, status=405)
