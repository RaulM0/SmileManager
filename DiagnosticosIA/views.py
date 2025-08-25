from django.shortcuts import render, get_object_or_404
from Pacientes.models import ImagenesClinicas
from ultralytics import YOLO
import os
from django.core.files import File
from SmileManager import settings

model_path = os.path.join('train_model', 'best.pt')
model = YOLO(model_path)

# Create your views here.
def diagnosticos(request):
    imagenes = ImagenesClinicas.objects.all()
    return render(request, 'diagnosticos/diagnosticos.html', {'imagenes': imagenes})

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
    
