"""RFC 6238 TOTP, encrypted seeds and hashed one-use recovery codes."""
import base64
import hashlib
import hmac
import secrets
import struct
import time
from datetime import timedelta
from urllib.parse import quote, urlencode

from cryptography.fernet import Fernet, MultiFernet, InvalidToken
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.core import signing
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed

from Usuarios.models import MFAChallenge

SALT = 'smile-mfa-challenge-v1'


def cipher():
    return MultiFernet([Fernet(key.encode()) for key in settings.MFA_ENCRYPTION_KEYS])


def totp(secret, counter, digits=6):
    digest = hmac.new(base64.b32decode(secret), struct.pack('>Q', counter), hashlib.sha1).digest()
    offset = digest[-1] & 15
    number = struct.unpack('>I', digest[offset:offset + 4])[0] & 0x7fffffff
    return str(number % (10 ** digits)).zfill(digits)


def verify_code(device, code):
    if len(code) == 6 and code.isascii() and code.isdigit():
        try:
            secret = cipher().decrypt(device.secret_ciphertext.encode()).decode()
        except InvalidToken:
            raise AuthenticationFailed('No se pudo verificar el segundo factor.') from None
        counter = int(time.time()) // 30
        for step in (counter, counter - 1, counter + 1):
            if step > device.last_counter and hmac.compare_digest(totp(secret, step), code):
                device.last_counter = step
                device.save(update_fields=['last_counter'])
                return True
    for encoded in device.recovery_hashes:
        if check_password(code, encoded):
            device.recovery_hashes = [value for value in device.recovery_hashes if value != encoded]
            device.save(update_fields=['recovery_hashes'])
            return True
    return False


def enrollment_counter(encrypted, code):
    if len(code) != 6 or not code.isascii() or not code.isdigit():
        return None
    secret = cipher().decrypt(encrypted.encode()).decode()
    counter = int(time.time()) // 30
    return next((step for step in (counter, counter - 1, counter + 1) if hmac.compare_digest(totp(secret, step), code)), None)


def new_challenge(user, *, enrollment):
    encrypted = ''
    if enrollment:
        encrypted = cipher().encrypt(base64.b32encode(secrets.token_bytes(20))).decode()
    challenge = MFAChallenge.objects.create(
        user=user, credential_hash=user.get_session_auth_hash(), enrollment_ciphertext=encrypted,
        expires_at=timezone.now() + timedelta(minutes=5),
    )
    return signing.dumps({'id': str(challenge.pk)}, salt=SALT)


def challenge_id(raw):
    try:
        return signing.loads(raw, salt=SALT, max_age=300)['id']
    except (signing.BadSignature, KeyError, TypeError):
        raise AuthenticationFailed('Verificación expirada o inválida.') from None


def enrollment_data(challenge, username):
    secret = cipher().decrypt(challenge.enrollment_ciphertext.encode()).decode()
    label = quote(f'SmileManager:{username}', safe='')
    return {'secret': secret, 'otpauth_uri': f'otpauth://totp/{label}?' + urlencode({'secret': secret, 'issuer': 'SmileManager', 'algorithm': 'SHA1', 'digits': 6, 'period': 30})}


def recovery_codes():
    codes = [secrets.token_hex(8) for _ in range(10)]
    return codes, [make_password(code) for code in codes]
