"""Fail closed for every former global clinical API, before view dispatch."""
import re

from django.conf import settings
from django.http import JsonResponse


LEGACY_CLINICAL_PATH = re.compile(
    r'^/api/v1/(?:dashboard|patients|appointments|consultations|clinical-images|diagnostics|exports)(?:/|\.|$)'
)


class LegacyClinicalAPIMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not settings.LEGACY_CLINICAL_API_ENABLED and LEGACY_CLINICAL_PATH.match(request.path_info):
            response = JsonResponse({
                'detail': 'La API clínica global fue retirada. Selecciona una clínica y utiliza /api/v1/clinics/.',
                'code': 'legacy_api_retired',
            }, status=410)
            response['Cache-Control'] = 'no-store'
            return response
        return self.get_response(request)
