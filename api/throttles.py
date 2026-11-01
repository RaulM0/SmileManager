import hashlib
import hmac
from functools import wraps
from django.conf import settings
from django.http import HttpResponse
from rest_framework.throttling import SimpleRateThrottle


class AddressThrottle(SimpleRateThrottle):
    scope = 'authentication'

    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': request.META.get('REMOTE_ADDR', 'unknown')}


class AccountThrottle(SimpleRateThrottle):
    scope = 'authentication_account'

    def get_cache_key(self, request, view):
        username = str(request.data.get('username', ''))[:150].casefold()
        if not username:
            return None
        digest = hmac.new(settings.SECRET_KEY.encode(), username.encode(), hashlib.sha256).hexdigest()
        return self.cache_format % {'scope': self.scope, 'ident': digest}


class UserThrottle(SimpleRateThrottle):
    scope = None

    def get_cache_key(self, request, view):
        identity = str(request.user.pk) if request.user.is_authenticated else request.META.get('REMOTE_ADDR', 'unknown')
        return self.cache_format % {'scope': self.scope, 'ident': identity}


class ExpensiveThrottle(UserThrottle):
    scope = 'expensive'


class EmailThrottle(UserThrottle):
    scope = 'email'


class ExportThrottle(UserThrottle):
    scope = 'export'


def limit_legacy(*classes, methods=('POST',)):
    def decorate(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if request.method in methods:
                # Django requests expose POST; DRF exposes data.
                request.data = request.POST
                for throttle_class in classes:
                    throttle = throttle_class()
                    if not throttle.allow_request(request, None):
                        response = HttpResponse('Demasiadas solicitudes.', status=429)
                        response['Retry-After'] = str(max(1, int(throttle.wait() or 1)))
                        return response
            return view(request, *args, **kwargs)
        return wrapped
    return decorate
