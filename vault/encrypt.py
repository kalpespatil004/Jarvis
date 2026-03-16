"""
vault/encrypt.py  –  AES-256 encryption (client-side)
"""

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import base64
import os

_SALT_SIZE = 16
_NONCE_SIZE = 12
_ITERATIONS = 100_000


def _derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=_ITERATIONS,
    )
    return kdf.derive(password.encode())


def encrypt(plaintext: str, password: str) -> str:
    """Encrypt plaintext with password. Returns base64-encoded ciphertext."""
    salt  = os.urandom(_SALT_SIZE)
    nonce = os.urandom(_NONCE_SIZE)
    key   = _derive_key(password, salt)
    aesgcm = AESGCM(key)
    ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
    blob = salt + nonce + ct
    return base64.b64encode(blob).decode()


def decrypt(ciphertext: str, password: str) -> str:
    """Decrypt base64-encoded ciphertext with password."""
    blob  = base64.b64decode(ciphertext.encode())
    salt  = blob[:_SALT_SIZE]
    nonce = blob[_SALT_SIZE:_SALT_SIZE + _NONCE_SIZE]
    ct    = blob[_SALT_SIZE + _NONCE_SIZE:]
    key   = _derive_key(password, salt)
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ct, None).decode()
