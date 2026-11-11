import hashlib
import hmac
from django.conf import settings
from rest_framework.throttling import SimpleRateThrottle
from .rate_limit import client_address, consume_window, identity_digest


class SharedRateThrottle(SimpleRateThrottle):
    def allow_request(self, request, view):
        if not settings.THROTTLE_REDIS_URL:
            # Explicitly limited to development/test by production settings.
            return super().allow_request(request, view)
        if self.rate is None:
            return True
        key = self.get_cache_key(request, view)
        if key is None:
            return True
        allowed, self.retry_after = consume_window(key, self.num_requests, self.duration)
        return allowed

    def wait(self):
        if settings.THROTTLE_REDIS_URL:
            return self.retry_after
        return super().wait()


class AddressThrottle(SharedRateThrottle):
    scope = 'authentication'

    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': identity_digest(client_address(request))}


class AccountThrottle(SharedRateThrottle):
    scope = 'authentication_account'

    def get_cache_key(self, request, view):
        username = str(request.data.get('username', ''))[:150].casefold()
        if not username:
            return None
        digest = hmac.new(settings.SECRET_KEY.encode(), username.encode(), hashlib.sha256).hexdigest()
        return self.cache_format % {'scope': self.scope, 'ident': digest}


class PasswordResetIPThrottle(AddressThrottle):
    scope = 'password_reset_ip'


class PasswordResetAccountThrottle(SharedRateThrottle):
    scope = 'password_reset_account'

    def get_cache_key(self, request, view):
        raw = request.data.get('email', '') if isinstance(request.data, dict) else ''
        if not isinstance(raw, str):
            return None
        email = raw.strip().casefold()[:254]
        if not email:
            return None
        digest = hmac.new(settings.SECRET_KEY.encode(), email.encode(), hashlib.sha256).hexdigest()
        return self.cache_format % {'scope': self.scope, 'ident': digest}


class PasswordResetConfirmThrottle(AddressThrottle):
    scope = 'password_reset_confirm'


class MFAChallengeThrottle(SharedRateThrottle):
    scope = 'mfa_challenge'

    def get_cache_key(self, request, view):
        raw = request.data.get('challenge', '') if hasattr(request.data, 'get') else ''
        return self.cache_format % {'scope': self.scope, 'ident': identity_digest(str(raw)[:2048])}


class UserThrottle(SharedRateThrottle):
    scope = None

    def get_cache_key(self, request, view):
        identity = f'user:{request.user.pk}' if request.user.is_authenticated else f'ip:{client_address(request)}'
        return self.cache_format % {'scope': self.scope, 'ident': identity_digest(identity)}


class ExpensiveThrottle(UserThrottle):
    scope = 'expensive'


class ReauthenticationThrottle(UserThrottle):
    scope = 'reauthentication'


class EmailThrottle(UserThrottle):
    scope = 'email'


class ExportThrottle(UserThrottle):
    scope = 'export'
