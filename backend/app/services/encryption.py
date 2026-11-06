from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings

KNOWN_PREFIXES = ("hf_", "gsk_", "csk_")


class DecryptionError(Exception):
    pass


@lru_cache
def _fernet() -> Fernet:
    return Fernet(settings.encryption_key.encode())


def encrypt(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise DecryptionError() from exc


def mask_token(token: str) -> str:
    tail = token[-4:] if len(token) >= 4 else token
    for prefix in KNOWN_PREFIXES:
        if token.startswith(prefix):
            return f"{prefix}****{tail}"
    return f"****{tail}"
