"""Proxy trust, outage behavior, and real Redis concurrency across processes."""
import multiprocessing
import os
import time
import django
from concurrent.futures import ThreadPoolExecutor
from unittest import skipUnless
from unittest.mock import patch
from uuid import uuid4

from django.core.cache import cache
from django.test import SimpleTestCase, override_settings
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from api.rate_limit import client_address, consume_window, redis_client
from api.throttles import AddressThrottle

TEST_REDIS = os.environ.get('RATE_LIMIT_TEST_REDIS_URL', '')


def process_attempts(args):
    url, prefix = args
    with override_settings(THROTTLE_REDIS_URL=url, THROTTLE_KEY_PREFIX=prefix):
        return sum(consume_window('processes', 7, 30)[0] for _ in range(10))


class ProtectedOperation(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [AddressThrottle]

    def post(self, request):
        return Response({'ok': True})


class ProxyTrustTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.factory = APIRequestFactory()

    @override_settings(THROTTLE_TRUSTED_PROXIES=[])
    def test_untrusted_client_cannot_spoof_address(self):
        request = self.factory.get('/', REMOTE_ADDR='203.0.113.10', HTTP_X_FORWARDED_FOR='198.51.100.2')
        self.assertEqual(client_address(request), '203.0.113.10')

    @override_settings(THROTTLE_TRUSTED_PROXIES=['10.0.0.0/24'])
    def test_walks_chain_from_trusted_peer_and_ignores_spoofed_prefix(self):
        request = self.factory.get('/', REMOTE_ADDR='10.0.0.2', HTTP_X_FORWARDED_FOR='192.0.2.99, 198.51.100.2, 10.0.0.1')
        self.assertEqual(client_address(request), '198.51.100.2')

    @override_settings(THROTTLE_TRUSTED_PROXIES=['2001:db8:1::/64'])
    def test_ipv6_chain(self):
        request = self.factory.get('/', REMOTE_ADDR='2001:db8:1::2', HTTP_X_FORWARDED_FOR='2001:db8:2::1')
        self.assertEqual(client_address(request), '2001:db8:2::1')

    @override_settings(THROTTLE_TRUSTED_PROXIES=['10.0.0.0/24'])
    def test_malformed_trusted_header_is_rejected(self):
        request = self.factory.post('/', REMOTE_ADDR='10.0.0.2', HTTP_X_FORWARDED_FOR='bad-value')
        self.assertEqual(ProtectedOperation.as_view()(request).status_code, 400)

    @override_settings(THROTTLE_REDIS_URL='redis://unused.invalid/0')
    def test_redis_failure_denies_operation_without_leaking_connection(self):
        from redis.exceptions import ConnectionError
        with patch('api.rate_limit.redis_client') as client, self.assertLogs('api.rate_limit', level='WARNING') as logs:
            client.return_value.eval.side_effect = ConnectionError('secret-url-do-not-log')
            response = ProtectedOperation.as_view()(self.factory.post('/'))
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('secret-url', str(response.data) + str(logs.output))

    @override_settings(THROTTLE_REDIS_URL='')
    def test_local_mode_still_limits(self):
        with patch.object(AddressThrottle, 'rate', '1/min', create=True):
            self.assertEqual(ProtectedOperation.as_view()(self.factory.post('/')).status_code, 200)
            self.assertEqual(ProtectedOperation.as_view()(self.factory.post('/')).status_code, 429)


@skipUnless(TEST_REDIS, 'Requires isolated RATE_LIMIT_TEST_REDIS_URL')
class RedisWindowTests(SimpleTestCase):
    def setUp(self):
        self.prefix = f'smile:test:{uuid4().hex}'
        self.context = override_settings(THROTTLE_REDIS_URL=TEST_REDIS, THROTTLE_KEY_PREFIX=self.prefix)
        self.context.enable()
        self.addCleanup(self.context.disable)
        self.addCleanup(self.cleanup_keys)

    def cleanup_keys(self):
        client = redis_client(TEST_REDIS)
        for key in client.scan_iter(match=f'{self.prefix}:*'):
            client.delete(key)

    def test_parallel_requests_obey_one_shared_limit(self):
        with ThreadPoolExecutor(max_workers=16) as pool:
            accepted = list(pool.map(lambda _: consume_window('parallel', 5, 30)[0], range(40)))
        self.assertEqual(sum(accepted), 5)

    def test_independent_processes_share_the_limit(self):
        with multiprocessing.get_context('spawn').Pool(4, initializer=django.setup) as pool:
            counts = pool.map_async(process_attempts, [(TEST_REDIS, self.prefix)] * 4).get(timeout=45)
        self.assertEqual(sum(counts), 7)

    def test_expiry_and_rejected_attempts_do_not_extend_window(self):
        self.assertTrue(consume_window('expiry', 1, 0.15)[0])
        allowed, retry = consume_window('expiry', 1, 0.15)
        self.assertFalse(allowed)
        self.assertGreater(retry, 0)
        self.assertLessEqual(retry, 0.15)
        time.sleep(0.2)
        self.assertTrue(consume_window('expiry', 1, 0.15)[0])

    def test_scope_isolation_and_state_survive_new_connection(self):
        self.assertTrue(consume_window('login', 1, 30)[0])
        redis_client.cache_clear()
        self.assertFalse(consume_window('login', 1, 30)[0])
        self.assertTrue(consume_window('export', 1, 30)[0])

    def test_http_429_has_retry_after_and_private_keys(self):
        factory = APIRequestFactory()
        with patch.object(AddressThrottle, 'rate', '1/min', create=True):
            self.assertEqual(ProtectedOperation.as_view()(factory.post('/', REMOTE_ADDR='203.0.113.10')).status_code, 200)
            response = ProtectedOperation.as_view()(factory.post('/', REMOTE_ADDR='203.0.113.10'))
        self.assertEqual(response.status_code, 429)
        self.assertGreater(int(response['Retry-After']), 0)
        keys = list(redis_client(TEST_REDIS).scan_iter(match=f'{self.prefix}:*'))
        self.assertNotIn(b'203.0.113.10', b''.join(keys))
