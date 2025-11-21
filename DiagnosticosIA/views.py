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
    imagenes = ImagenesClinicas.objects.filter(paciente__medico=request.user).select_related('paciente')
    
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
    img_path = imagen_obj.imagen.path

    # Directorio temporal de escritura en el servidor (ej: /tmp/detecciones)
    temp_results_dir = os.path.join(settings.MEDIA_ROOT, 'detecciones_yolo')
    os.makedirs(temp_results_dir, exist_ok=True)
    
    output_file = None # Inicializar la variable de ruta del archivo de salida
    detecciones = []

    try:
        # Ejecutar la detección. YOLO creará una subcarpeta (pred) dentro de temp_results_dir
        results = model.predict(
            img_path,
            save=True,
            project=temp_results_dir, # Usamos el directorio temporal
            name='pred'
        )

        # 1. Encontrar el archivo de imagen generado por YOLO
        save_dir = str(results[0].save_dir) # La ruta final que YOLO usó (ej: /tmp/media/detecciones_yolo/pred)
        
        for file in os.listdir(save_dir):
            if file.lower().endswith(('.jpg', '.png', '.jpeg', '.webp')):
                output_file = os.path.join(save_dir, file)
                break

        if not output_file or not os.path.exists(output_file):
            raise FileNotFoundError(f"No se encontró la imagen procesada en {save_dir}")

        # 2. Subir el resultado a S3 usando el campo de Django
        with open(output_file, 'rb') as f:
            # .save() con django-storages subirá el archivo a S3
            imagen_obj.resultados.save(os.path.basename(output_file), File(f), save=True)

        # 3. Extraer información de las detecciones
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
            'error': f"Error al ejecutar YOLO: {str(e)}"
        })

    finally:
        # 4. Limpieza: Eliminar el directorio temporal de la instancia
        if os.path.exists(temp_results_dir):
             import shutil
             shutil.rmtree(temp_results_dir, ignore_errors=True)

    return render(request, 'diagnosticos/resultados.html', {
        'imagen': imagen_obj,
        'detecciones': detecciones,
        'results_image': imagen_obj.resultados.url # Esto apuntará a la URL de S3
    })
