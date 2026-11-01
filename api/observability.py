"""Metadatos operativos: sin URL con IDs, headers ni contenido clínico."""
import json
import logging
import time

logger = logging.getLogger('smile.access')


class RequestLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.perf_counter()
        response = self.get_response(request)
        if getattr(request, 'request_id', None) and 'X-Request-ID' not in response:
            response['X-Request-ID'] = str(request.request_id)
        match = getattr(request, 'resolver_match', None)
        route = match.view_name if match else 'unresolved'
        if route not in ('health-live', 'health-ready'):
            logger.info('%s', json.dumps({
                'event': 'http_request',
                'request_id': str(getattr(request, 'request_id', '')),
                'endpoint': route,
                'method': request.method,
                'status': response.status_code,
                'duration_ms': round((time.perf_counter() - start) * 1000, 2),
            }))
        return response
