from django.shortcuts import render, get_object_or_404
from Pacientes.models import ImagenesClinicas
import logging
from django.core.paginator import Paginator
from .services import analyze_clinical_image

# Create your views here.

logger = logging.getLogger(__name__)

def diagnosticos(request):
    imagenes = ImagenesClinicas.objects.filter(paciente__medico=request.user).select_related('paciente').order_by('-fecha_subida')
    
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

def resultados(request, imagen_id):
    imagen_obj = get_object_or_404(ImagenesClinicas, id=imagen_id, paciente__medico=request.user)
    
    try:
        detecciones = analyze_clinical_image(imagen_obj)

    except Exception as e:
        logger.exception('Error al analizar la imagen clínica %s', imagen_id)
        return render(request, 'diagnosticos/resultados.html', {
            'imagen': imagen_obj,
            'error': f"Error al ejecutar YOLO: {str(e)}"
        }, status=500)

    return render(request, 'diagnosticos/resultados.html', {
        'imagen': imagen_obj,
        'detecciones': detecciones,
        'results_image': imagen_obj.resultados.url  # URL de S3
    })
