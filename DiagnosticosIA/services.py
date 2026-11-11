import os
import shutil
import tempfile
import hashlib
from functools import lru_cache
from django.conf import settings
from django.core.files.base import ContentFile
from threading import Lock

@lru_cache(maxsize=1)
def model_version():
    digest = hashlib.sha256()
    with open(os.path.join(settings.BASE_DIR, 'train_model', 'best.pt'), 'rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


# The model artifact remains immutable for the lifetime of this process.
_model = None
_model_lock = Lock()
_inference_lock = Lock()


def get_model():
    """Load the optional inference engine once, only when analysis is requested."""
    global _model
    with _model_lock:
        if _model is None:
            from ultralytics import YOLO

            model_version()
            _model = YOLO(os.path.join(settings.BASE_DIR, 'train_model', 'best.pt'))
        return _model


class ClinicalImageMissingError(Exception):
    """The source referenced by the clinical record is absent from storage."""


class ClinicalImageChangedError(Exception):
    """La imagen cambió después de calcular la huella."""


def analyze_clinical_image_detached(image, *, expected_hash=None):
    """Run inference without changing the image record or persistent storage."""
    temp_input=None; temp_results=None
    try:
        if not image.imagen:
            raise ClinicalImageMissingError
        suffix=os.path.splitext(image.imagen.name)[1] or '.jpg'
        try:
            image.imagen.open('rb')
        except FileNotFoundError as exc:
            raise ClinicalImageMissingError from exc
        with tempfile.NamedTemporaryFile(delete=False,suffix=suffix) as temporary:
            temp_input=temporary.name
            try:
                digest = hashlib.sha256()
                for chunk in iter(lambda: image.imagen.read(1024 * 1024), b''):
                    digest.update(chunk)
                    temporary.write(chunk)
                if expected_hash and digest.hexdigest() != expected_hash:
                    raise ClinicalImageChangedError
            finally: image.imagen.close()
        temp_results=tempfile.mkdtemp(prefix='yolo_results_')
        model = get_model()
        # Ultralytics keeps mutable predictor state on its model instance.
        with _inference_lock:
            results = model.predict(temp_input, save=True, project=temp_results, name='pred')
        save_dir=str(results[0].save_dir)
        supported_outputs=('.jpg','.jpeg','.png','.webp','.gif','.bmp','.tif','.tiff')
        output=next((os.path.join(save_dir,name) for name in os.listdir(save_dir) if name.lower().endswith(supported_outputs)),None)
        if not output or not os.path.exists(output): raise FileNotFoundError(f'No se encontró la imagen procesada en {save_dir}')
        if os.path.getsize(output) > getattr(settings, 'CLINICAL_AI_RESULT_MAX_BYTES', 32 * 1024 * 1024):
            raise ValueError('El resultado del análisis supera el límite permitido.')
        with open(output, 'rb') as result_file:
            result_bytes = result_file.read()
        detections = [{'clase':model.names[int(cls)],'confianza':float(results[0].boxes.conf[index]),'coordenadas':results[0].boxes.xyxy[index].tolist()} for index,cls in enumerate(results[0].boxes.cls)]
        return detections, os.path.basename(output), result_bytes
    finally:
        if temp_input and os.path.exists(temp_input): os.remove(temp_input)
        if temp_results and os.path.exists(temp_results): shutil.rmtree(temp_results,ignore_errors=True)


def analyze_clinical_image(image, *, expected_hash=None):
    detections, filename, result_bytes = analyze_clinical_image_detached(image, expected_hash=expected_hash)
    image.resultados.save(filename, ContentFile(result_bytes), save=True)
    return detections
