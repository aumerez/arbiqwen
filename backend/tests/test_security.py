"""Tests for the security hardening: upload limit and config guards."""

from app.config import DEV_JWT_SECRET, Settings


def _settings(**kw):
    return Settings(_env_file=None, **kw)


def test_jwt_secret_default_detection():
    assert _settings().jwt_secret_is_default is True
    assert _settings(JWT_SECRET="a-real-secret-value-that-is-32-bytes-long").jwt_secret_is_default is False


def test_is_production_flag():
    assert _settings(ENVIRONMENT="development").is_production is False
    assert _settings(ENVIRONMENT="production").is_production is True


def test_max_upload_bytes():
    assert _settings(MAX_UPLOAD_SIZE_MB=25).max_upload_bytes == 25 * 1024 * 1024


def test_dev_jwt_secret_meets_min_length():
    # The default must satisfy the field's min_length so the app boots in dev.
    assert len(DEV_JWT_SECRET) >= 32


async def test_upload_rejects_oversized_file(client, auth_headers, monkeypatch):
    from app.documents import routes

    monkeypatch.setattr(routes.settings, "MAX_UPLOAD_SIZE_MB", 0, raising=False)
    big = {"file": ("big.txt", b"x" * 2048, "text/plain")}
    r = await client.post("/documents/upload", headers=auth_headers, files=big)
    assert r.status_code == 413
