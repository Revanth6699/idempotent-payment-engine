from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from jose import jwt

from backend.app.services.token_service import TokenService


def test_create_and_decode_access_token():
    user_id = uuid4()

    token = TokenService.create_access_token(user_id)

    assert token
    assert isinstance(token, str)

    decoded_user_id = TokenService.decode_access_token(token)

    assert decoded_user_id == user_id


def test_decode_access_token_rejects_invalid_token():
    with pytest.raises(ValueError, match="Invalid or expired access token"):
        TokenService.decode_access_token("invalid.jwt.token")


def test_decode_access_token_rejects_wrong_token_type():
    user_id = uuid4()

    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "type": TokenService.REFRESH_TOKEN_TYPE,
        "iat": now,
        "exp": now + timedelta(minutes=15),
    }

    token = jwt.encode(
        payload,
        TokenService.JWT_SECRET_KEY,
        algorithm=TokenService.JWT_ALGORITHM,
    )

    with pytest.raises(ValueError, match="Invalid access token type"):
        TokenService.decode_access_token(token)


def test_create_refresh_token():
    refresh_token = TokenService.create_refresh_token()

    assert refresh_token
    assert isinstance(refresh_token, str)

    # token_urlsafe(48) produces a substantially long
    # cryptographically random opaque token.
    assert len(refresh_token) >= 64


def test_refresh_token_hashing():
    refresh_token = TokenService.create_refresh_token()

    token_hash = TokenService.hash_refresh_token(refresh_token)

    assert token_hash
    assert isinstance(token_hash, str)
    assert len(token_hash) == 64

    # Same token must always produce the same SHA-256 hash.
    assert (
        TokenService.hash_refresh_token(refresh_token)
        == token_hash
    )

    # Different token must produce a different hash.
    another_refresh_token = TokenService.create_refresh_token()

    assert (
        TokenService.hash_refresh_token(another_refresh_token)
        != token_hash
    )


def test_refresh_token_expiry():
    before = datetime.now(timezone.utc)

    expiry = TokenService.get_refresh_token_expiry()

    after = datetime.now(timezone.utc)

    expected_minimum = before + timedelta(
        days=TokenService.REFRESH_TOKEN_EXPIRE_DAYS
    )
    expected_maximum = after + timedelta(
        days=TokenService.REFRESH_TOKEN_EXPIRE_DAYS
    )

    assert expected_minimum <= expiry <= expected_maximum
    