"""Cryptographic primitives for identity, signing, and encryption."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import uuid

from .core.common import to_canonical_json


def compute_signature(secret: str, workspace_uuid: str, name: str) -> str:
    """HMAC-SHA256(secret, uuid:name) — agent identity verification."""
    return hmac.new(
        secret.encode(), f"{workspace_uuid}:{name}".encode(), hashlib.sha256
    ).hexdigest()


def compute_checksum(value: object) -> str:
    """SHA-256 of canonical JSON — content integrity checksum."""
    canonical = to_canonical_json(value)
    return hashlib.sha256(canonical.encode()).hexdigest()


def hash_ip(ip: str, secret: str) -> str:
    """HMAC-SHA256(secret, ip) truncated to 16 hex chars — privacy-preserving IP hash."""
    return hmac.new(
        secret.encode(), ip.encode(), hashlib.sha256
    ).hexdigest()[:16]


def compute_uuid_token(base: str, secret: str) -> str:
    """HMAC-SHA256(secret, base) truncated to 8 hex chars — UUID integrity suffix."""
    return hmac.new(
        secret.encode(), base.encode(), hashlib.sha256
    ).hexdigest()[:8]


def generate_uuid(secret: str) -> str:
    """Generate a tamper-proof workspace UUID."""
    base = str(uuid.uuid4())
    token = compute_uuid_token(base, secret)
    return f"{base}-{token}"


def is_valid_uuid(workspace_uuid: str, secret: str) -> bool:
    """Verify UUID suffix matches HMAC token."""
    if not workspace_uuid or len(workspace_uuid) != 36 + 1 + 8:
        return False
    base = workspace_uuid[:36]
    token = workspace_uuid[37:]
    expected = compute_uuid_token(base, secret)
    return token == expected


def encrypt(data: bytes, key: bytes) -> bytes:
    """AES-GCM encryption with random 12-byte IV."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    iv = os.urandom(12)
    ciphertext = AESGCM(key).encrypt(iv, data, None)
    return iv + ciphertext


def decrypt(data: bytes, key: bytes) -> bytes:
    """AES-GCM decryption."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    iv = data[:12]
    ciphertext = data[12:]
    return AESGCM(key).decrypt(iv, ciphertext, None)


def compute_hmac(secret: str, payload: str) -> str:
    """HMAC-SHA256(secret, payload) — general-purpose signing."""
    return hmac.new(
        secret.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()
