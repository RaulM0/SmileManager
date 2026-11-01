from datetime import date, datetime
import os
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from SmileManager import settings
from .models import Consentimiento, Paciente, AntescedentesMedicos, Consulta, ImagenesClinicas, Odontograma, EstudioComparativo
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
import pandas as pd
from django.core.mail import send_mail
from django.db.models.functions import Concat
from django.db.models import Value
import json
from .forms import EstudioComparativoForm
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_GET
from django.http import FileResponse
from .PDF import pdf_progreso
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from api.policies import scoped, owned_or_404, consistent_or_404
from api.upload_policy import validate_upload
from api.services.exports import export_patients, export_consultations, export_images
from django.core.exceptions import ValidationError
from api.serializers import MedicalHistorySerializer, OdontogramSerializer, PatientSerializer
from api.services.patients import deactivate_patient
from api.services.clinical_records import save_record
from rest_framework.exceptions import APIException
from api.throttles import limit_legacy, EmailThrottle, ExportThrottle




# Create your views here.

@require_GET
def clinical_session_file(request, kind, resource_id, field):
    from django.http import Http404
    allowed = {
        'image': (ImagenesClinicas, {'imagen', 'resultados'}),
        'study': (EstudioComparativo, {'antes_oclusal_superior', 'antes_lateral_izquierda', 'antes_frontal', 'antes_lateral_derecha', 'antes_oclusal_inferior', 'despues_perfil', 'despues_semiperfil', 'despues_retrato_frontal', 'despues_retrato_sonrisa'}),
        'consent': (Consentimiento, {'archivo_ine', 'pdf_generado'}),
    }
    if kind not in allowed or field not in allowed[kind][1]:
        raise Http404
    model = allowed[kind][0]
    obj = owned_or_404(request.user, model, pk=resource_id)
    file = getattr(obj, field)
    if not file:
        raise Http404
    try:
        response = FileResponse(file.open('rb'), as_attachment=kind == 'consent', filename=os.path.basename(file.name))
    except FileNotFoundError:
        raise Http404
    response['Cache-Control'] = 'private, no-store'
    return response


def menuPacientes(request):
    return render(request, 'pacientes/menuPacientes.html')

from django.contrib import messages
from django.shortcuts import render, redirect
from datetime import datetime
from .models import Paciente

def registrar_paciente(request):
    if request.method == 'POST':
        serializer = PatientSerializer(data=request.POST, context={'request': request})
        if not serializer.is_valid():
            messages.error(request, 'Revisa los datos del paciente.')
            return render(request, 'pacientes/registroPacientes.html')
        try:
            patient = serializer.save()
        except APIException:
            messages.error(request, 'Revisa los datos del paciente.')
            return render(request, 'pacientes/registroPacientes.html')
        request.audit_resource_id = patient.pk
        request.audit_success = True
        messages.success(request, "Registro exitoso de paciente.")
        return redirect('/registroPacientes/registrar_pacientes/')
    
    return render(request, 'pacientes/registroPacientes.html')


def todos_los_pacientes(request):
    pacientes = scoped(request.user, Paciente).order_by('appat')
    return render(request, 'pacientes/todosPacientes.html',{'pacientes': pacientes})

def buscar_pacientes(request):
    query = request.GET.get('q', '').strip()
    pacientes = scoped(request.user, Paciente).order_by('appat')

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
    paciente = scoped(request.user, Paciente).filter(id=id).first()
    if not paciente:
        messages.error(request, 'Paciente no encontrado')
        return redirect('buscar_pacientes')
    else:
        edad = (datetime.today().date() - paciente.fecha_nacimiento).days // 365
        return render(request, 'pacientes/verPaciente.html', {'paciente': paciente, 'edad': edad})
    
def editar_paciente(request, id):
    paciente = scoped(request.user, Paciente).filter(id=id).first()
    if not paciente:
        messages.error(request, 'Paciente no encontrado')
        return redirect('buscar_pacientes')

    if request.method == 'POST':
        serializer = PatientSerializer(paciente, data=request.POST, partial=True, context={'request': request})
        if not serializer.is_valid():
            messages.error(request, 'Revisa los datos del paciente.')
            return render(request, 'pacientes/editarPaciente.html', {'paciente': paciente})
        try:
            serializer.save()
        except APIException:
            messages.error(request, 'Revisa los datos del paciente.')
            return render(request, 'pacientes/editarPaciente.html', {'paciente': paciente})
        request.audit_success = True
        messages.success(request, "Paciente actualizado exitosamente.")
        return redirect('buscar_pacientes')

    return render(request, 'pacientes/editarPaciente.html', {'paciente': paciente})

#la eliminacion ed logica, que el campo estatus cambie a inactivo
def eliminar_paciente(request, id):
    paciente = scoped(request.user, Paciente).filter(id=id).first()
    if not paciente:
        messages.error(request, 'Paciente no encontrado')
        return redirect('buscar_pacientes')

    if request.method == 'POST':
        deactivate_patient(paciente)
        request.audit_success = True
        messages.success(request, "Paciente eliminado exitosamente.")
    
    return redirect('buscar_pacientes')

# Vistas del historial médico
def menu_historial(request):
    paciente_seleccionado = None
    paciente_id = request.GET.get('paciente_id')

    if paciente_id:
        try:
            paciente_seleccionado = scoped(request.user, Paciente).get(id=paciente_id)
        except Paciente.DoesNotExist:
            paciente_seleccionado = None

    return render(request, 'historialMedico/menuHistorial.html', {
        'paciente_seleccionado': paciente_seleccionado
    })

def buscar_pacientes_ajax(request):
    term = request.GET.get('term', '')
    pacientes = scoped(request.user, Paciente).filter(nombre__icontains=term)[:10]

    results = []
    for p in pacientes:
        results.append({
            'id': p.id,
            'text': f'{p.nombre} {p.appat} {p.apmat}'
        })
    return JsonResponse({'results': results})

def antecedentes(request, id):
    paciente = owned_or_404(request.user, Paciente, id=id)
    
    antecedentes = consistent_or_404(request.user, AntescedentesMedicos, paciente).first()
    created = antecedentes is None
    if antecedentes is None:
        antecedentes = AntescedentesMedicos(paciente=paciente, medico=request.user)
    
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

        changes = {field: (None if form_data[field] == '' else form_data[field]) for field in bool_fields if field in form_data}
        for field, source in [('alergias', 'alergias_txt'), ('medicamentos', 'medicamentos'), ('cirugias_previas', 'cirugias_previas'), ('otros', 'otros')]:
            if source in form_data:
                changes[field] = form_data[source]
        serializer = MedicalHistorySerializer(antecedentes, data=changes, partial=True)
        if not serializer.is_valid():
            return JsonResponse({'detail': 'Datos de antecedentes inválidos.'}, status=400)
        try:
            version = int(form_data.get('version', ''))
            antecedentes = save_record(user=request.user, patient_id=id, model=AntescedentesMedicos, changes=serializer.validated_data, expected_version=version)
        except ValueError:
            return JsonResponse({'detail': 'Versión requerida.'}, status=400)
        except APIException as exc:
            return JsonResponse({'detail': str(exc.detail)}, status=exc.status_code)

        return JsonResponse({
            'status': 'success',
            'message': 'Antecedentes creados' if created else 'Antecedentes actualizados',
            'version': antecedentes.version,
        })

    context = {
        'paciente': paciente,
        'antecedentes': antecedentes,
    }
    return render(request, 'historialMedico/antecedentes.html', context)

        
def consultas(request, id):
    paciente = owned_or_404(request.user, Paciente, id=id)
    fecha = datetime.today().date().strftime('%Y-%m-%d')
    
    if request.method == 'POST':
        motivo_consulta = request.POST.get('motivo_consulta', '').upper()
        diagnostico = request.POST.get('diagnostico', 'Ninguno').upper()
        tratamiento = request.POST.get('tratamiento', 'Ninguno').upper()
        observaciones = request.POST.get('observaciones', 'Ninguna').upper()
        
        nueva_consulta = Consulta.objects.create(
            paciente=paciente,
            medico=request.user,  # Asignamos el médico logueado
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
    consulta = owned_or_404(request.user, Consulta, id=id)
    return render(request, 'receta/receta.html', {'consulta': consulta})

def historial_consultas(request, id):
    paciente = owned_or_404(request.user, Paciente, id=id)
    consultas = scoped(request.user, Consulta).filter(paciente=paciente).order_by('-fecha_consulta')
    return render(request, 'historialMedico/historial_consultas.html', {'consultas': consultas, 'paciente': paciente})

# Vistas para imágenes clínicas
def imagenes_clinicas(request, id):
    paciente = owned_or_404(request.user, Paciente, id=id)
    return render(request, 'imagenes/imagenes_clinicas.html', {'paciente': paciente})

def cargar_imagen(request, id):
    paciente = owned_or_404(request.user, Paciente, id=id)
    consultas = scoped(request.user, Consulta).filter(paciente=paciente).order_by('-fecha_consulta')

    if request.method == 'POST':
        consulta_id = request.POST.get('consulta_id')
        tipo_imagen = request.POST.get('tipo', '').strip().upper()
        descripcion = request.POST.get('descripcion', 'Ninguna').strip().upper()
        imagen = request.FILES.get('archivo')

        if not imagen:
            messages.error(request, "Por favor, sube una imagen.")
            return render(request, 'imagenes/cargarImagen.html', {'paciente': paciente, 'consultas': consultas})

        try:
            validate_upload(imagen)
        except ValidationError as exc:
            messages.error(request, exc.messages[0])
            return render(request, 'imagenes/cargarImagen.html', {'paciente': paciente, 'consultas': consultas}, status=400)

        if not tipo_imagen or not descripcion:
            messages.error(request, "Todos los campos son obligatorios.")
            return render(request, 'imagenes/cargarImagen.html', {'paciente': paciente, 'consultas': consultas})

        if not consulta_id or not consulta_id.isdigit():
            messages.error(request, "Debes seleccionar una consulta válida.")
            return render(request, 'imagenes/cargarImagen.html', {'paciente': paciente, 'consultas': consultas})

        consulta = owned_or_404(request.user, Consulta, id=consulta_id, paciente=paciente)

        clinical_image = ImagenesClinicas.objects.create(
            paciente=paciente,
            consulta=consulta,
            medico=request.user,  # Asignamos el médico
            tipo_imagen=tipo_imagen,
            descripcion=descripcion,
            imagen=imagen
        )
        request.audit_resource_id = clinical_image.pk
        request.audit_success = True

        messages.success(request, "Imagen clínica cargada exitosamente.")
        return redirect('cargar_imagen', paciente.id)

    return render(request, 'imagenes/cargarImagen.html', {'paciente': paciente, 'consultas': consultas})


def buscar_imagen(request, id):
    paciente = owned_or_404(request.user, Paciente, id=id)
    consultas = scoped(request.user, Consulta).filter(paciente=paciente).order_by('-fecha_consulta')
    imagenes = scoped(request.user, ImagenesClinicas).filter(paciente=paciente)
    
    # Obtención mediante GET
    fecha = request.GET.get('fecha')
    consulta_id = request.GET.get('consulta_id')
    
    if fecha:
        imagenes = imagenes.filter(fecha_subida__date=fecha)
    
    if consulta_id and consulta_id.isdigit():
        imagenes = imagenes.filter(consulta__id=consulta_id, consulta__medico=request.user)
    
    return render(request, 'imagenes/buscar_imagen.html', {
        'paciente': paciente,
        'consultas': consultas,
        'imagenes': imagenes
    })

@require_POST
def eliminar_imagen(request, imagen_id):
    imagen = owned_or_404(request.user, ImagenesClinicas, id=imagen_id)
    paciente_id = imagen.paciente.id  # Para redirigir después

    imagen.delete()
    request.audit_success = True
    messages.success(request, "Imagen clínica eliminada correctamente.")

    return redirect('buscar_imagen', paciente_id)


def historial_imagenes(request, id):
    paciente = owned_or_404(request.user, Paciente, id=id)
    imagenes = scoped(request.user, ImagenesClinicas).filter(paciente=paciente).order_by('-fecha_subida')
    return render(request, 'imagenes/historial_imagenes.html', {
        'paciente': paciente,
        'imagenes': imagenes
    })


# Exportacion de datos a Excel
def exportar_datos(request):
    return render(request, 'pacientes/exportar_datos.html')

@limit_legacy(ExportThrottle, methods=('GET',))
def exportar_pacientes(request):
    return export_patients(request.user)


@limit_legacy(ExportThrottle, methods=('GET',))
def exportar_consultas(request):
    return export_consultations(request.user)

    
@limit_legacy(ExportThrottle, methods=('GET',))
def exportar_imagenes(request):
    return export_images(request.user)
    
# Vista para contactar pacientes
def contactar_pacientes(request):
    paciente_seleccionado = None
    paciente_id = request.GET.get('selectPaciente')

    if paciente_id:
        try:
            paciente_seleccionado = scoped(request.user, Paciente).get(id=paciente_id)
        except Paciente.DoesNotExist:
            paciente_seleccionado = None

    return render(request, 'pacientes/contactar_pacientes.html', {
        'paciente_seleccionado': paciente_seleccionado
    })

    
def contacto(request, id):
    paciente = owned_or_404(request.user, Paciente, id=id)
    return render(request, 'pacientes/contacto.html', {'paciente': paciente})


# Mandar un mensaje al paciente
@limit_legacy(EmailThrottle)
def enviar_mensaje(request):
    if request.method == "POST":
        asunto = request.POST.get("asunto")
        mensaje = request.POST.get("mensaje")
        paciente_id = request.POST.get("paciente_id")

        if not (asunto and mensaje and paciente_id):
            messages.error(request, "Por favor completa todos los campos.")
            return redirect('enviar_mensaje')

        # Validar que el paciente exista y pertenezca al médico
        paciente = owned_or_404(request.user, Paciente, id=paciente_id)
        destinatario = paciente.email

        # --- versión texto plano ---
        texto = (
            f"{mensaje}\n\n"
            f"Atentamente,\nClínica Dental Sonrisa Perfecta 🦷"
        )

        # --- versión HTML ---
        contexto = {'asunto': asunto, 'mensaje': mensaje, 'paciente': paciente, 'user': request.user}
        html = render_to_string('emails/mensaje_paciente.html', contexto)

        correo = EmailMultiAlternatives(
            asunto,
            texto,
            settings.EMAIL_HOST_USER,
            [destinatario]
        )
        correo.attach_alternative(html, 'text/html')
        correo.send()

        messages.success(request, f"Correo enviado exitosamente a {destinatario}.")
        return redirect('enviar_mensaje')

    return render(request, "pacientes/contactar_pacientes.html")



def odontograma(request, id):
    paciente = owned_or_404(request.user, Paciente, id=id)
    
    # Tomamos el odontograma más reciente del paciente
    odontograma_obj = consistent_or_404(request.user, Odontograma, paciente).order_by('-created').first()
    
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
        'odontograma_data': odontograma_data,
        'odontograma_version': odontograma_obj.version if odontograma_obj else 0,
    }
    
    return render(request, 'odontograma/odontograma.html', context)



@require_POST
def guardar_odontograma(request, paciente_id):
    paciente = owned_or_404(request.user, Paciente, id=paciente_id)
    consistent_or_404(request.user, Odontograma, paciente)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except (ValueError, UnicodeDecodeError):
            return JsonResponse({'detail': 'JSON inválido.'}, status=400)
        if not isinstance(data, dict):
            return JsonResponse({'detail': 'Odontograma inválido.'}, status=400)
        serializer = OdontogramSerializer(data=data)
        if not serializer.is_valid():
            return JsonResponse({'detail': 'Odontograma inválido.'}, status=400)
        try:
            odontograma = save_record(user=request.user, patient_id=paciente_id, model=Odontograma, changes=serializer.validated_data, expected_version=data.get('version'))
        except APIException as exc:
            return JsonResponse({'detail': str(exc.detail)}, status=exc.status_code)

        return JsonResponse({
            'status': 'ok',
            'mensaje': 'Odontograma guardado',
            'id': odontograma.id,
            'version': odontograma.version,
        })

    return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'}, status=405)


#Progreso del paciente (Before & After)

def progreso(request, paciente_id):
    paciente = owned_or_404(request.user, Paciente, id=paciente_id)
    estudio = consistent_or_404(request.user, EstudioComparativo, paciente).order_by('-fecha_creacion').first()
    form = EstudioComparativoForm(instance=estudio)
    visualizar_activado = True if estudio else False
    
    context = {
        'paciente': paciente,
        'form': form,              
        'estudio': estudio,          
        'visualizar_activado': visualizar_activado
    }
    
    # Asegúrate de que el path del template sea el correcto
    return render(request, 'before_after/progreso.html', context)

def estudio_comparativo_view(request, paciente_id):
    paciente = owned_or_404(request.user, Paciente, id=paciente_id)
    estudio = consistent_or_404(request.user, EstudioComparativo, paciente).first()

    if request.method == 'POST':
        try:
            for uploaded in request.FILES.values():
                validate_upload(uploaded)
        except ValidationError as exc:
            messages.error(request, exc.messages[0])
            return render(request, 'before_after/estudio_comparativo.html', {'paciente': paciente, 'form': EstudioComparativoForm(instance=estudio), 'estudio': estudio}, status=400)
        form = EstudioComparativoForm(request.POST, request.FILES, instance=estudio)
        if form.is_valid():
            nuevo_estudio = form.save(commit=False)
            nuevo_estudio.paciente = paciente
            nuevo_estudio.medico = request.user
            nuevo_estudio.save()
            messages.success(request, "✅ El estudio se ha guardado correctamente.")
            return redirect('estudio_comparativo', paciente_id=paciente.id)
        else:
            messages.error(request, "⚠️ Ocurrió un error al guardar el estudio. Verifica los datos ingresados.")
    else:
        form = EstudioComparativoForm(instance=estudio)

    context = {
        'paciente': paciente,
        'form': form,
        'estudio': estudio,
        'visualizar_activado': estudio is not None,
    }
    return render(request, 'before_after/estudio_comparativo.html', context)

def visualizar_estudio(request, paciente_id):
    paciente = owned_or_404(request.user, Paciente, id=paciente_id)
    estudio = get_object_or_404(consistent_or_404(request.user, EstudioComparativo, paciente))

    # Calcular edad
    edad = None
    if paciente.fecha_nacimiento:
        hoy = date.today()
        edad = hoy.year - paciente.fecha_nacimiento.year - (
            (hoy.month, hoy.day) < (paciente.fecha_nacimiento.month, paciente.fecha_nacimiento.day)
        )

    context = {
        'paciente': paciente,
        'estudio': estudio,
        'edad': edad if edad is not None else "N/A"
    }

    return render(request, 'before_after/estudio_comparativo.html', context)

def descargar_pdf_estudio(request, paciente_id):
    return pdf_progreso(request, paciente_id)

# Consentimiento Informado

def consentimiento_informado(request, paciente_id):
    paciente = owned_or_404(request.user, Paciente, id=paciente_id)
    
    # Crear o recuperar consentimiento asignando medico
    consentimiento = consistent_or_404(request.user, Consentimiento, paciente).first()
    if consentimiento is None:
        consentimiento = Consentimiento(paciente=paciente, medico=request.user, texto='')

    # Verificar si ya fue aceptado
    form_activo = not bool(consentimiento.fecha_aceptacion)

    if request.method == 'POST' and form_activo:
        texto = request.POST.get('texto', '')
        archivo_ine = request.FILES.get('archivo_ine')

        # Validación de archivo
        if archivo_ine:
            try:
                validate_upload(archivo_ine, allow_pdf=True)
            except ValidationError as exc:
                messages.error(request, exc.messages[0])
                return redirect('consentimiento', paciente_id=paciente.id)

            consentimiento.archivo_ine = archivo_ine

        consentimiento.texto = texto
        consentimiento.fecha_aceptacion = timezone.now()
        consentimiento.save()

        messages.success(request, "Consentimiento guardado correctamente.")
        return redirect('menu_historial')

    context = {
        'paciente': paciente,
        'consentimiento': consentimiento,
        'form_activo': form_activo
    }
    return render(request, 'consentimiento/consentimiento.html', context)
