from django.shortcuts import get_object_or_404
from django.http import Http404, HttpResponse
from django.template.loader import get_template
from django.conf import settings
from xhtml2pdf import pisa
from io import BytesIO
from datetime import date
import os
from urllib.parse import urljoin
from .models import Paciente, EstudioComparativo


# --- Añade estos imports ---
from django.conf import settings
import os

# --- Añade esta función FUERA de tu vista ---
def link_callback(uri, rel):
    """
    Convierte URLs de HTML (ej. /media/foto.jpg) en rutas
    absolutas del sistema de archivos (ej. /home/user/proyecto/media/foto.jpg)
    """
    # Maneja archivos de MEDIA
    media_url = settings.MEDIA_URL  # Usualmente '/media/'
    media_root = settings.MEDIA_ROOT  # Usualmente '/ruta/a/tu/proyecto/media'
    
    # Maneja archivos STATIC (para tu CSS, si tuvieras)
    static_url = settings.STATIC_URL
    static_root = settings.STATIC_ROOT

    if uri.startswith(media_url):
        # Quita el /media/ y pégalo al MEDIA_ROOT
        path = os.path.join(media_root, uri.replace(media_url, "", 1))
    elif uri.startswith(static_url):
        # Quita el /static/ y pégalo al STATIC_ROOT
        path = os.path.join(static_root, uri.replace(static_url, "", 1))
    else:
        return uri  # No es un archivo local

    # Asegurarse de que el archivo exista
    if not os.path.isfile(path):
        # print(f"Archivo no encontrado: {path}") # Útil para debug
        return None
    return path


# --- Tu vista, ahora MÁS SIMPLE ---
def pdf_progreso(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    estudio = EstudioComparativo.objects.filter(paciente=paciente).order_by('-fecha_creacion').first()
    
    if not estudio:
        raise Http404(f"No se encontró ningún estudio para {paciente.nombre}.")
    
    # ... (cálculo de edad es igual) ...
    if paciente.fecha_nacimiento:
        hoy = date.today()
        edad = hoy.year - paciente.fecha_nacimiento.year - ((hoy.month, hoy.day) < (paciente.fecha_nacimiento.month, paciente.fecha_nacimiento.day))
    else:
        edad = "N/A"

    # --- El contexto es MÁS FÁCIL ---
    # Simplemente pasamos el objeto de imagen. 
    # El template usará .url
    context = {
        "paciente": paciente,
        "edad": edad,
        "fecha_tratamiento": estudio.fecha_inicio,
        
        "antes_oclusal_superior": estudio.antes_oclusal_superior,
        "antes_lateral_izquierda": estudio.antes_lateral_izquierda,
        "antes_frontal": estudio.antes_frontal,
        "antes_lateral_derecha": estudio.antes_lateral_derecha,
        "antes_oclusal_inferior": estudio.antes_oclusal_inferior,

        "despues_perfil": estudio.despues_perfil,
        "despues_semiperfil": estudio.despues_semiperfil,
        "despues_retrato_frontal": estudio.despues_retrato_frontal,
        "despues_retrato_sonrisa": estudio.despues_retrato_sonrisa,
    }

    template = get_template("before_after/formato_estudio.html")
    html = template.render(context)

    buffer = BytesIO()
    
    # --- CAMBIO CLAVE AQUÍ ---
    # Le pasamos el link_callback a pisa
    pisa_status = pisa.CreatePDF(
        html.encode('utf-8'),
        dest=buffer,
        encoding='utf-8',
        link_callback=link_callback  # <--- ¡LA MAGIA!
    )

    if pisa_status.err:
        return HttpResponse(f"❌ Error al generar PDF: {pisa_status.err}", status=500)

    # ... (el resto es igual) ...
    buffer.seek(0)
    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="Estudio_{paciente.nombre}_{paciente.appat}.pdf"'
    return response