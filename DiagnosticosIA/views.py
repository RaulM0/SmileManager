from django.shortcuts import render, get_object_or_404
from Pacientes.models import ImagenesClinicas
import logging
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from .services import ClinicalImageMissingError, analyze_clinical_image
from .services import ClinicalImageChangedError
from .runs import execute as execute_analysis
from api.policies import scoped, owned_or_404
from api.throttles import limit_legacy, ExpensiveThrottle

# Create your views here.

logger = logging.getLogger(__name__)

def diagnosticos(request):
    imagenes = scoped(request.user, ImagenesClinicas).select_related('paciente').order_by('-fecha_subida')
    
    # Filtros
    paciente_filter = request.GET.get('paciente')
    tipo_filter = request.GET.get('tipo_imagen')
    fecha_filter = request.GET.get('fecha')
    
    if paciente_filter:
        imagenes = imagenes.filter(paciente__nombre__icontains=paciente_filter)
    
    if tipo_filter:
        imagenes = imagenes.filter(tipo_imagen=tipo_filter)
    
    if fecha_filter:
        imagenes = imagenes.filter(fecha_subida__date=fecha_filter)
    
    # Estadísticas
    imagenes_procesadas = imagenes.filter(resultados__isnull=False).count()
    imagenes_pendientes = imagenes.filter(resultados__isnull=True).count()
    total_imagenes = imagenes.count()
    
    porcentaje_procesadas = round((imagenes_procesadas / total_imagenes * 100), 2) if total_imagenes > 0 else 0
    tipos_count = imagenes.values('tipo_imagen').distinct().count()
    
    # Paginación
    paginator = Paginator(imagenes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'diagnosticos/diagnosticos.html', {
        'imagenes': page_obj,
        'imagenes_procesadas': imagenes_procesadas,
        'imagenes_pendientes': imagenes_pendientes,
        'porcentaje_procesadas': porcentaje_procesadas,
        'tipos_count': tipos_count,
    })

@require_http_methods(['GET', 'POST'])
@limit_legacy(ExpensiveThrottle)
def resultados(request, imagen_id):
    imagen_obj = owned_or_404(request.user, ImagenesClinicas, id=imagen_id)
    if request.method == 'GET':
        return render(request, 'diagnosticos/resultados.html', {'imagen': imagen_obj})
    try:
        run, disposition = execute_analysis(user=request.user, image_id=imagen_obj.pk, request_id=request.request_id, force=request.POST.get('force') == 'true', analyzer=analyze_clinical_image)
        if disposition == 'running':
            return render(request, 'diagnosticos/resultados.html', {'imagen': imagen_obj, 'error': 'Ya hay un análisis en curso. Vuelve a consultar en unos momentos.'}, status=202)
        detecciones = run.detections
        imagen_obj.refresh_from_db()

    except ClinicalImageMissingError:
        return render(request, 'diagnosticos/resultados.html', {
            'imagen': imagen_obj,
            'error': 'La imagen original no está disponible. Recupera el archivo original o vuelve a cargarlo en el expediente.'
        }, status=404)
    except ClinicalImageChangedError:
        return render(request, 'diagnosticos/resultados.html', {'imagen': imagen_obj, 'error': 'La imagen cambió durante el análisis.'}, status=409)
    except Exception:
        logger.error('Fallo de análisis de imagen clínica id=%s request_id=%s', imagen_id, request.request_id)
        return render(request, 'diagnosticos/resultados.html', {
            'imagen': imagen_obj,
            'error': 'No se pudo analizar la imagen. Inténtalo de nuevo.'
        }, status=500)

    return render(request, 'diagnosticos/resultados.html', {
        'imagen': imagen_obj,
        'detecciones': detecciones,
        'results_image': reverse('clinical-session-file', args=['image', imagen_obj.pk, 'resultados']) if imagen_obj.resultados else None,
    })
