"""HTTP adapter for SmileIA. Inference and model artifacts live outside Django."""
import base64
import hashlib
import math
import os
import re

import requests
from django.conf import settings
from django.core.files.base import ContentFile


class ClinicalImageMissingError(Exception):
    """The source referenced by the clinical record is absent from storage."""


class ClinicalImageChangedError(Exception):
    """La imagen cambió después de calcular la huella."""


class AIServiceError(Exception):
    """The private inference service is unavailable or returned invalid data."""


def _request(path, *, data=None, headers=None):
    url = settings.SMILEIA_URL.rstrip('/')
    token = settings.SMILEIA_TOKEN
    if not url or not token:
        raise AIServiceError('SmileIA no está configurado.')
    limit = getattr(settings, 'CLINICAL_AI_RESULT_MAX_BYTES', 32 * 1024 * 1024)
    try:
        with requests.request(
            'GET' if data is None else 'POST', url + path, data=data,
            headers={'Authorization': 'Bearer ' + token, **(headers or {})},
            timeout=(5, settings.SMILEIA_TIMEOUT), stream=True, allow_redirects=False,
        ) as response:
            if response.status_code != 200:
                raise AIServiceError('SmileIA no pudo completar la solicitud.')
            body = bytearray()
            for chunk in response.iter_content(64 * 1024):
                body.extend(chunk)
                if len(body) > limit * 2 + 1024 * 1024:
                    raise AIServiceError('Respuesta de SmileIA demasiado grande.')
            import json
            result = json.loads(body)
            if not isinstance(result, dict):
                raise ValueError('Invalid response')
            return result
    except (requests.RequestException, ValueError) as exc:
        raise AIServiceError('Respuesta inválida de SmileIA.') from exc


def model_version():
    version = _request('/v1/model').get('model_version')
    if not isinstance(version, str) or not re.fullmatch('[0-9a-f]{64}', version):
        raise AIServiceError('Versión inválida de SmileIA.')
    return version


def analyze_clinical_image_detached(image, *, expected_hash=None, expected_version=None):
    if not image.imagen:
        raise ClinicalImageMissingError
    try:
        with image.imagen.open('rb') as source:
            data = source.read(settings.SMILEIA_INPUT_MAX_BYTES + 1)
    except FileNotFoundError as exc:
        raise ClinicalImageMissingError from exc
    if len(data) > settings.SMILEIA_INPUT_MAX_BYTES:
        raise AIServiceError('La imagen supera el límite de SmileIA.')
    digest = hashlib.sha256(data).hexdigest()
    if expected_hash and digest != expected_hash:
        raise ClinicalImageChangedError
    version = expected_version or model_version()
    payload = _request('/v1/analyze', data=data, headers={
        'Content-Type': 'application/octet-stream', 'X-Input-SHA256': digest,
        'X-Model-Version': version,
    })
    try:
        if payload['model_version'] != version:
            raise ValueError('Model changed')
        detections = payload['detections']
        if not isinstance(detections, list):
            raise ValueError('Invalid detections')
        for detection in detections:
            if (not isinstance(detection['clase'], str)
                    or not 0 <= float(detection['confianza']) <= 1
                    or len(detection['coordenadas']) != 4
                    or not all(math.isfinite(float(x)) for x in detection['coordenadas'])):
                raise ValueError('Invalid detection')
        filename = os.path.basename(payload['filename'])
        if not filename or os.path.splitext(filename)[1].lower() not in ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.tif', '.tiff'):
            raise ValueError('Invalid filename')
        result = base64.b64decode(payload['result'], validate=True)
        if not result or len(result) > getattr(settings, 'CLINICAL_AI_RESULT_MAX_BYTES', 32 * 1024 * 1024):
            raise ValueError('Invalid result size')
        return detections, filename, result
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise AIServiceError('Resultado inválido de SmileIA.') from exc


def analyze_clinical_image(image, *, expected_hash=None, expected_version=None):
    detections, filename, result = analyze_clinical_image_detached(
        image, expected_hash=expected_hash, expected_version=expected_version)
    image.resultados.save(filename, ContentFile(result), save=True)
    return detections
