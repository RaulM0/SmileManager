"""Atomic sliding windows shared by every worker; no credentials in Redis keys."""
import hashlib
import hmac
import logging
from functools import lru_cache
from ipaddress import ip_address, ip_network
from uuid import uuid4

from django.conf import settings
from rest_framework.exceptions import APIException, ParseError

logger = logging.getLogger(__name__)

# The server clock avoids disagreement between application instances. Rejected
# attempts do not extend the window or create unbounded entries.
WINDOW_SCRIPT = """
local stamp = redis.call('TIME')
local now = tonumber(stamp[1]) * 1000 + math.floor(tonumber(stamp[2]) / 1000)
local duration = tonumber(ARGV[1])
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', now - duration)
if redis.call('ZCARD', KEYS[1]) >= tonumber(ARGV[2]) then
    local oldest = redis.call('ZRANGE', KEYS[1], 0, 0, 'WITHSCORES')
    return {0, math.max(1, tonumber(oldest[2]) + duration - now)}
end
redis.call('ZADD', KEYS[1], now, ARGV[3])
redis.call('PEXPIRE', KEYS[1], duration)
return {1, 0}
"""


class RateLimitUnavailable(APIException):
    status_code = 503
    default_detail = 'El servicio de protección de acceso no está disponible. Inténtalo más tarde.'
    default_code = 'rate_limit_unavailable'


def identity_digest(identity):
    return hmac.new(settings.SECRET_KEY.encode(), identity.encode(), hashlib.sha256).hexdigest()


def client_address(request):
    """Ignore XFF from untrusted peers; traverse trusted chains right to left."""
    try:
        peer = ip_address(request.META.get('REMOTE_ADDR', ''))
        trusted = tuple(ip_network(cidr) for cidr in settings.THROTTLE_TRUSTED_PROXIES)
        if not any(peer in network for network in trusted):
            return str(peer)
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if not forwarded:
            return str(peer)
        if len(forwarded) > 2048 or forwarded.count(',') >= 32:
            raise ValueError
        chain = [ip_address(part.strip()) for part in forwarded.split(',')]
        for address in reversed(chain):
            if not any(address in network for network in trusted):
                return str(address)
        return str(chain[0])
    except ValueError:
        raise ParseError('Dirección de cliente inválida.') from None


@lru_cache(maxsize=4)
def redis_client(url):
    from redis import Redis

    return Redis.from_url(url, socket_connect_timeout=2, socket_timeout=2,
                          max_connections=32, decode_responses=False)


def consume_window(key, count, duration):
    from redis.exceptions import RedisError

    try:
        allowed, retry_ms = redis_client(settings.THROTTLE_REDIS_URL).eval(
            WINDOW_SCRIPT, 1, f'{settings.THROTTLE_KEY_PREFIX}:{key}',
            int(duration * 1000), count, uuid4().hex,
        )
        return bool(allowed), retry_ms / 1000
    except RedisError:
        # Exceptions and URLs may contain credentials; never log either.
        logger.warning('Rate limiter unavailable')
        raise RateLimitUnavailable() from None
