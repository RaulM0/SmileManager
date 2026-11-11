"""Streaming authenticated backup codec. Decryption emits only verified plaintext."""
import os
import sys
import tempfile
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

MAGIC = b'SMILEBACKUP1\0'
key = bytes.fromhex(os.environ['BACKUP_KEY'])
if len(key) != 32:
    raise SystemExit('A 256-bit backup key is required.')
source, target = sys.stdin.buffer, sys.stdout.buffer
if sys.argv[1] == 'encrypt':
    nonce = os.urandom(12)
    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce)).encryptor()
    cipher.authenticate_additional_data(MAGIC)
    target.write(MAGIC + nonce)
    while chunk := source.read(65536):
        target.write(cipher.update(chunk))
    target.write(cipher.finalize() + cipher.tag)
elif sys.argv[1] == 'decrypt':
    if source.read(len(MAGIC)) != MAGIC:
        raise SystemExit('Invalid encrypted backup.')
    nonce = source.read(12)
    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce)).decryptor()
    cipher.authenticate_additional_data(MAGIC)
    with tempfile.TemporaryFile() as verified:
        tail = b''
        while chunk := source.read(65536):
            block = tail + chunk
            if len(block) > 16:
                verified.write(cipher.update(block[:-16]))
                tail = block[-16:]
            else:
                tail = block
        try:
            verified.write(cipher.finalize_with_tag(tail))
        except Exception:
            raise SystemExit('Backup authentication failed; no plaintext emitted.') from None
        verified.seek(0)
        while chunk := verified.read(65536):
            target.write(chunk)
else:
    raise SystemExit('Use encrypt or decrypt.')
