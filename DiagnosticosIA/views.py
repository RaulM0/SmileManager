from django.shortcuts import render, get_object_or_404
from Pacientes.models import ImagenesClinicas
from ultralytics import YOLO
import os
from django.core.files import File
from SmileManager import settings
from django.core.paginator import Paginator
from django.db.models import Count

# Create your views here.

model_path = os.path.join('train_model', 'best.pt')
model = YOLO(model_path)

def diagnosticos(request):
    imagenes = ImagenesClinicas.objects.all().select_related('paciente')
    
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
    # Obtener la imagen clínica
    imagen_obj = get_object_or_404(ImagenesClinicas, id=imagen_id)
    img_path = imagen_obj.imagen.path

    try:
        # Ejecutar la detección
        results = model.predict(
            img_path,
            save=True,
            project=os.path.join(settings.MEDIA_ROOT, 'detecciones'),
            name='pred'
        )

        # Obtener la ruta de la imagen generada
        save_dir = str(results[0].save_dir)
        output_file = None
        for file in os.listdir(save_dir):
            if file.lower().endswith(('.jpg', '.png', '.jpeg', '.webp')):
                output_file = os.path.join(save_dir, file)
                break

        if not output_file or not os.path.exists(output_file):
            raise FileNotFoundError(f"No se encontró la imagen procesada en {save_dir}")

        # Guardar el resultado en ImageField
        with open(output_file, 'rb') as f:
            imagen_obj.resultados.save(os.path.basename(output_file), File(f), save=True)

        # Extraer información de las detecciones para mostrar en la plantilla
        detecciones = []
        boxes = results[0].boxes
        for i, cls in enumerate(boxes.cls):
            detecciones.append({
                'clase': model.names[int(cls)],
                'confianza': float(boxes.conf[i]),
                'coordenadas': boxes.xyxy[i].tolist()
            })

    except Exception as e:
        return render(request, 'diagnosticos/resultados.html', {
            'imagen': imagen_obj,
            'error': str(e)
        })

    return render(request, 'diagnosticos/resultados.html', {
        'imagen': imagen_obj,
        'detecciones': detecciones,
        'results_image': imagen_obj.resultados.url
    })
    
