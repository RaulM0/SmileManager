import hashlib
import hmac
from django.conf import settings
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
