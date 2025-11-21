from django.shortcuts import render, get_object_or_404
from Pacientes.models import ImagenesClinicas
from ultralytics import YOLO
import os
from django.core.files import File
from SmileManager import settings
from django.core.paginator import Paginator
from django.db.models import Count
import requests
from io import BytesIO
import tempfile

# Create your views here.

model_path = os.path.join('train_model', 'best.pt')
model = YOLO(model_path)

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
    
    # Como la imagen está en S3, necesitamos descargarla temporalmente
    temp_input_file = None
    temp_results_dir = None
    detecciones = []

    try:
        # 1. Descargar la imagen desde S3 a un archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            # Obtener la URL de S3 y descargar
            response = requests.get(imagen_obj.imagen.url)
            response.raise_for_status()
            tmp_file.write(response.content)
            temp_input_file = tmp_file.name
        
        # 2. Crear directorio temporal para resultados
        temp_results_dir = tempfile.mkdtemp(prefix='yolo_results_')
        
        # 3. Ejecutar la detección
        results = model.predict(
            temp_input_file,
            save=True,
            project=temp_results_dir,
            name='pred'
        )

        # 4. Encontrar el archivo de imagen generado por YOLO
        save_dir = str(results[0].save_dir)
        output_file = None
        
        for file in os.listdir(save_dir):
            if file.lower().endswith(('.jpg', '.png', '.jpeg', '.webp')):
                output_file = os.path.join(save_dir, file)
                break

        if not output_file or not os.path.exists(output_file):
            raise FileNotFoundError(f"No se encontró la imagen procesada en {save_dir}")

        # 5. Subir el resultado a S3 usando el campo de Django
        with open(output_file, 'rb') as f:
            imagen_obj.resultados.save(os.path.basename(output_file), File(f), save=True)

        # 6. Extraer información de las detecciones
        boxes = results[0].boxes
        for i, cls in enumerate(boxes.cls):
            detecciones.append({
                'clase': model.names[int(cls)],
                'confianza': float(boxes.conf[i]),
                'coordenadas': boxes.xyxy[i].tolist()
            })

    except requests.RequestException as e:
        return render(request, 'diagnosticos/resultados.html', {
            'imagen': imagen_obj,
            'error': f"Error al descargar la imagen desde S3: {str(e)}"
        })
    
    except Exception as e:
        return render(request, 'diagnosticos/resultados.html', {
            'imagen': imagen_obj,
            'error': f"Error al ejecutar YOLO: {str(e)}"
        })

    finally:
        # 7. Limpieza: Eliminar archivos temporales
        if temp_input_file and os.path.exists(temp_input_file):
            try:
                os.remove(temp_input_file)
            except:
                pass
                
        if temp_results_dir and os.path.exists(temp_results_dir):
            import shutil
            shutil.rmtree(temp_results_dir, ignore_errors=True)

    return render(request, 'diagnosticos/resultados.html', {
        'imagen': imagen_obj,
        'detecciones': detecciones,
        'results_image': imagen_obj.resultados.url  # URL de S3
    })