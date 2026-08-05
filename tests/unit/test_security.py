import pytest
from app.utils.security import verify_password, get_password_hash, create_access_token, decode_access_token
from app.core.config import settings


def test_password_hash_and_verify():
    password = "TestPassword123!"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed)
    assert not verify_password("wrong", hashed)


def test_create_and_decode_token():
    data = {"sub": "1", "email": "test@example.com"}
    token = create_access_token(data)
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "1"
    assert decoded["email"] == "test@example.com"


def test_decode_invalid_token():
    assert decode_access_token("invalid.token.here") is None
