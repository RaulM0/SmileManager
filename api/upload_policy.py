"""Validación de uploads antes de persistir o ejecutar inferencia."""
import os
import warnings

from django.conf import settings
from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError

FORMATS = {'JPEG': ({'.jpg', '.jpeg'}, 'image/jpeg'), 'PNG': ({'.png'}, 'image/png'), 'GIF': ({'.gif'}, 'image/gif'), 'WEBP': ({'.webp'}, 'image/webp')}


def validate_upload(upload, *, allow_pdf=False):
    max_bytes = getattr(settings, 'CLINICAL_UPLOAD_MAX_BYTES', 5 * 1024 * 1024)
    max_pixels = getattr(settings, 'CLINICAL_UPLOAD_MAX_PIXELS', 20_000_000)
    if not upload or upload.size <= 0 or upload.size > max_bytes:
        raise ValidationError('El archivo está vacío o supera el límite permitido.')
    ext = os.path.splitext(upload.name)[1].lower()
    content_type = (getattr(upload, 'content_type', '') or '').lower().split(';')[0].strip()
    try:
        upload.seek(0)
        if allow_pdf and ext == '.pdf':
            data = upload.read()
            if not data.startswith(b'%PDF-') or b'%%EOF' not in data[-2048:] or content_type not in ('', 'application/pdf', 'application/octet-stream'):
                raise ValidationError('Documento PDF inválido.')
            return
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(upload) as image:
                info = FORMATS.get(image.format)
                if not info or ext not in info[0] or content_type not in ('', info[1], 'application/octet-stream'):
                    raise ValidationError('Formato, extensión o tipo de imagen inválido.')
                if image.width <= 0 or image.height <= 0 or image.width * image.height > max_pixels:
                    raise ValidationError('Dimensiones de imagen fuera del límite permitido.')
                image.verify()
            upload.seek(0)
            with Image.open(upload) as image:
                image.load()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValidationError('Archivo de imagen inválido.') from exc
    finally:
        upload.seek(0)
