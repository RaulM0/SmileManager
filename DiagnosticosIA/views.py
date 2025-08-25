from django.shortcuts import render, get_object_or_404
from Pacientes.models import ImagenesClinicas
from ultralytics import YOLO
import os
from django.core.files import File
from SmileManager import settings

model_path = os.path.join(settings.BASE_DIR, 'runs/detect/train3/weights/best.pt')
model = YOLO(model_path)

# Create your views here.
def diagnosticos(request):
    imagenes = ImagenesClinicas.objects.all()
    return render(request, 'diagnosticos/diagnosticos.html', {'imagenes': imagenes})


'''
def resultados(request, imagen_id):
    imagen_obj = get_object_or_404(ImagenesClinicas, id=imagen_id)
    img_path = imagen_obj.imagen.path

    # Ejecutar detección y forzar salida en media/detecciones/pred
    results = model.predict(
        img_path,
        save=True,
        project=os.path.join(settings.MEDIA_ROOT, 'detecciones'),
        name='pred'
    )

    # Carpeta donde YOLO guardó la predicción
    save_dir = results[0].save_dir  # devuelve un objeto Path de pathlib
    save_dir = str(save_dir)  # lo convertimos a string

    # Buscar cualquier archivo generado dentro de save_dir
    output_file = None
    for file in os.listdir(save_dir):
        if file.lower().endswith(('.jpg', '.png', '.jpeg', '.webp')):
            output_file = os.path.join(save_dir, file)
            break

    if not output_file or not os.path.exists(output_file):
        raise FileNotFoundError(f"No se encontró la imagen procesada en {save_dir}")

    # Guardar en el ImageField (Django moverá el archivo a MEDIA_ROOT/resultados/)
    with open(output_file, 'rb') as f:
        imagen_obj.resultados.save(os.path.basename(output_file), File(f), save=True)

    return render(request, 'diagnosticos/resultados.html', {
        'imagen': imagen_obj,
        'results': results
    })
'''

def resultados(request, imagen_id):
    imagen_obj = get_object_or_404(ImagenesClinicas, id = imagen_id)
    img_path = imagen_obj.imagen.path
    
    #Ejecutar deteccion
    results = model.predict(
        img_path,
        save=True,
        project=os.path.join(settings.MEDIA_ROOT, 'detecciones'),
        name='pred'
    )
    
    save_dir = str(results[0].save_dir)
    output_file = None
    for file in os.listdir(save_dir):
        if file.lower().endswith(('.jpg', '.png', '.jpeg', '.webp')):
            output_file = os.path.join(save_dir, file)
            break

    if not output_file or not os.path.exists(output_file):
        raise FileNotFoundError(f"No se encontró la imagen procesada en {save_dir}")

    # Guardar resultado en ImageField (opcional)
    with open(output_file, 'rb') as f:
        imagen_obj.resultados.save(os.path.basename(output_file), File(f), save=True)

    return render(request, 'diagnosticos/resultados.html', {
        'imagen': imagen_obj,
        'results': results
    })
        
    
