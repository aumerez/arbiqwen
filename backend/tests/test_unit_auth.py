"""Unit tests for password hashing and JWT."""

from app.auth.jwt import create_access_token, create_refresh_token, decode_token, hash_token
from app.auth.password import hash_password, verify_password


def test_password_roundtrip():
    h = hash_password("secret123")
    assert h != "secret123"
    assert verify_password("secret123", h) is True
    assert verify_password("wrong", h) is False


def test_jwt_roundtrip_carries_claims():
    token = create_access_token({"sub": "1", "email": "a@arbi.dev", "role": "admin"})
    payload = decode_token(token)
    assert payload["sub"] == "1"
    assert payload["email"] == "a@arbi.dev"
    assert payload["role"] == "admin"
    assert "exp" in payload and "jti" in payload


def test_jwt_invalid_returns_none():
    assert decode_token("not-a-token") is None


def test_refresh_tokens_are_unique():
    a = create_refresh_token({"sub": "1"})
    b = create_refresh_token({"sub": "1"})
    assert a != b
    assert hash_token(a) != hash_token(b)


def test_hash_token_is_stable():
    assert hash_token("abc") == hash_token("abc")
