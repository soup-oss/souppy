"""Tests for souppy crypto module."""

import pytest
from souppy.crypto import (
    compute_signature,
    compute_checksum,
    hash_ip,
    compute_uuid_token,
    generate_uuid,
    is_valid_uuid,
    compute_hmac,
)


def test_compute_signature():
    sig = compute_signature("secret123", "uuid-123", "alice")
    assert len(sig) == 64  # SHA-256 hex
    assert isinstance(sig, str)


def test_compute_signature_deterministic():
    sig1 = compute_signature("secret", "uuid", "alice")
    sig2 = compute_signature("secret", "uuid", "alice")
    assert sig1 == sig2


def test_compute_signature_different_inputs():
    sig1 = compute_signature("secret", "uuid", "alice")
    sig2 = compute_signature("secret", "uuid", "bob")
    assert sig1 != sig2


def test_compute_checksum():
    checksum = compute_checksum({"key": "value"})
    assert len(checksum) == 64
    assert isinstance(checksum, str)


def test_compute_checksum_deterministic():
    c1 = compute_checksum({"a": 1, "b": 2})
    c2 = compute_checksum({"b": 2, "a": 1})  # Different order, same canonical
    assert c1 == c2


def test_hash_ip():
    hashed = hash_ip("192.168.1.1", "secret")
    assert len(hashed) == 16
    assert isinstance(hashed, str)


def test_generate_uuid():
    uuid = generate_uuid("secret")
    assert len(uuid) == 36 + 1 + 8  # UUID + dash + token
    assert is_valid_uuid(uuid, "secret")


def test_is_valid_uuid():
    uuid = generate_uuid("secret")
    assert is_valid_uuid(uuid, "secret") is True
    assert is_valid_uuid(uuid, "wrong-secret") is False
    assert is_valid_uuid("invalid", "secret") is False


def test_compute_hmac():
    sig = compute_hmac("secret", "payload")
    assert len(sig) == 64
    assert isinstance(sig, str)
