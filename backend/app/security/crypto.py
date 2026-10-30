"""AES-256-GCM helpers for remembered provider keys."""

from __future__ import annotations

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class CryptoError(Exception):
    """Raised when encryption configuration or payloads are invalid."""


def _load_master_key(raw: str) -> bytes:
    if not raw:
        raise CryptoError("FOLIO_ENCRYPTION_KEY is not set")
    try:
        key = base64.b64decode(raw)
    except Exception as exc:
        raise CryptoError("FOLIO_ENCRYPTION_KEY must be base64") from exc
    if len(key) != 32:
        raise CryptoError("FOLIO_ENCRYPTION_KEY must decode to 32 bytes")
    return key


def encrypt_secret(plaintext: str, master_key_b64: str) -> tuple[bytes, bytes]:
    """Encrypt plaintext. Returns (ciphertext, nonce)."""
    key = _load_master_key(master_key_b64)
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return ciphertext, nonce


def decrypt_secret(ciphertext: bytes, nonce: bytes, master_key_b64: str) -> str:
    """Decrypt ciphertext with the given nonce."""
    key = _load_master_key(master_key_b64)
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")
