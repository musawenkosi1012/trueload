"""Ed25519 signing for passports; key auto-generated on first use."""
import base64
import os

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from config import Config


def _load_or_create() -> Ed25519PrivateKey:
    path = Config.PASSPORT_KEY_PATH
    if os.path.exists(path):
        with open(path, "rb") as f:
            return serialization.load_pem_private_key(f.read(), password=None)
    key = Ed25519PrivateKey.generate()
    with open(path, "wb") as f:
        f.write(key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption()))
    return key


def sign(message: bytes) -> str:
    return base64.b64encode(_load_or_create().sign(message)).decode()


def public_key_b64() -> str:
    pub = _load_or_create().public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return base64.b64encode(pub).decode()


def verify(message: bytes, signature_b64: str, pub_b64: str | None = None) -> bool:
    raw = base64.b64decode(pub_b64) if pub_b64 else None
    pub = (Ed25519PublicKey.from_public_bytes(raw) if raw
           else _load_or_create().public_key())
    try:
        pub.verify(base64.b64decode(signature_b64), message)
        return True
    except Exception:
        return False
