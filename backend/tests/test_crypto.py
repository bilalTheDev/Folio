"""AES-GCM round-trip tests."""

import base64
import os

import pytest

from backend.app.security.crypto import CryptoError, decrypt_secret, encrypt_secret


def test_encrypt_decrypt_round_trip() -> None:
    master = base64.b64encode(os.urandom(32)).decode("ascii")
    cipher, nonce = encrypt_secret("gsk_test_secret_key", master)
    assert decrypt_secret(cipher, nonce, master) == "gsk_test_secret_key"


def test_missing_master_key() -> None:
    with pytest.raises(CryptoError):
        encrypt_secret("secret", "")
