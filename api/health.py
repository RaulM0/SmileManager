from django.db import DatabaseError, connection
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET


@never_cache
@require_GET
def live(request):
    return JsonResponse({'status': 'ok'})


@never_cache
@require_GET
def ready(request):
    if settings.THROTTLE_REDIS_URL:
        from redis.exceptions import RedisError
        from .rate_limit import redis_client
        try:
            redis_client(settings.THROTTLE_REDIS_URL).ping()
        except RedisError:
            return JsonResponse({'status': 'unavailable'}, status=503)
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
    except DatabaseError:
        return JsonResponse({'status': 'unavailable'}, status=503)
    return JsonResponse({'status': 'ok'})
