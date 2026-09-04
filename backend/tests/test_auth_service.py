from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from backend.app.core.database import SessionLocal
from backend.app.models.refresh_token_model import RefreshToken
from backend.app.models.user_model import User
from backend.app.schemas.auth_schemas import UserRegisterRequest
from backend.app.services.auth_service import AuthService
from backend.app.services.token_service import TokenService


@pytest.fixture
def db():
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


def unique_email() -> str:
    return f"test-auth-{uuid4().hex}@example.com"


def cleanup_user(db, email: str) -> None:
    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if user is not None:
        db.query(RefreshToken).filter(
            RefreshToken.user_id == user.id
        ).delete(synchronize_session=False)

        db.delete(user)
        db.commit()


def test_register_user(db):
    email = unique_email()

    try:
        request = UserRegisterRequest(
            email=email,
            password="TestPassword123!",
        )

        user = AuthService.register_user(
            db=db,
            request=request,
        )

        assert user.id is not None
        assert user.email == email
        assert user.is_active is True

        assert user.password_hash != "TestPassword123!"
        assert user.password_hash.startswith("$argon2")

    finally:
        cleanup_user(db, email)


def test_register_user_normalizes_email(db):
    email = unique_email()

    try:
        request = UserRegisterRequest(
            email=email.upper(),
            password="TestPassword123!",
        )

        user = AuthService.register_user(
            db=db,
            request=request,
        )

        assert user.email == email.lower()

    finally:
        cleanup_user(db, email.lower())


def test_register_user_rejects_duplicate_email(db):
    email = unique_email()

    try:
        request = UserRegisterRequest(
            email=email,
            password="TestPassword123!",
        )

        AuthService.register_user(
            db=db,
            request=request,
        )

        with pytest.raises(
            ValueError,
            match="Email is already registered",
        ):
            AuthService.register_user(
                db=db,
                request=request,
            )

    finally:
        cleanup_user(db, email)


def test_authenticate_user_with_valid_credentials(db):
    email = unique_email()

    try:
        request = UserRegisterRequest(
            email=email,
            password="TestPassword123!",
        )

        registered_user = AuthService.register_user(
            db=db,
            request=request,
        )

        authenticated_user = AuthService.authenticate_user(
            db=db,
            email=email,
            password="TestPassword123!",
        )

        assert authenticated_user is not None
        assert authenticated_user.id == registered_user.id
        assert authenticated_user.email == email

    finally:
        cleanup_user(db, email)


def test_authenticate_user_rejects_wrong_password(db):
    email = unique_email()

    try:
        request = UserRegisterRequest(
            email=email,
            password="TestPassword123!",
        )

        AuthService.register_user(
            db=db,
            request=request,
        )

        authenticated_user = AuthService.authenticate_user(
            db=db,
            email=email,
            password="WrongPassword123!",
        )

        assert authenticated_user is None

    finally:
        cleanup_user(db, email)


def test_authenticate_user_rejects_inactive_user(db):
    email = unique_email()

    try:
        request = UserRegisterRequest(
            email=email,
            password="TestPassword123!",
        )

        user = AuthService.register_user(
            db=db,
            request=request,
        )

        user.is_active = False
        db.commit()

        authenticated_user = AuthService.authenticate_user(
            db=db,
            email=email,
            password="TestPassword123!",
        )

        assert authenticated_user is None

    finally:
        cleanup_user(db, email)


def test_login_creates_access_and_refresh_tokens(db):
    email = unique_email()

    try:
        request = UserRegisterRequest(
            email=email,
            password="TestPassword123!",
        )

        user = AuthService.register_user(
            db=db,
            request=request,
        )

        tokens = AuthService.login(
            db=db,
            email=email,
            password="TestPassword123!",
        )

        assert tokens.access_token
        assert tokens.refresh_token
        assert tokens.token_type == "bearer"

        stored_token = (
            db.query(RefreshToken)
            .filter(RefreshToken.user_id == user.id)
            .first()
        )

        assert stored_token is not None
        assert stored_token.token_hash == (
            TokenService.hash_refresh_token(
                tokens.refresh_token
            )
        )

    finally:
        cleanup_user(db, email)


def test_login_rejects_invalid_credentials(db):
    email = unique_email()

    try:
        request = UserRegisterRequest(
            email=email,
            password="TestPassword123!",
        )

        AuthService.register_user(
            db=db,
            request=request,
        )

        with pytest.raises(
            ValueError,
            match="Invalid email or password",
        ):
            AuthService.login(
                db=db,
                email=email,
                password="WrongPassword123!",
            )

    finally:
        cleanup_user(db, email)


def test_refresh_access_token_rotates_refresh_token(db):
    email = unique_email()

    try:
        request = UserRegisterRequest(
            email=email,
            password="TestPassword123!",
        )

        user = AuthService.register_user(
            db=db,
            request=request,
        )

        original_tokens = AuthService.login(
            db=db,
            email=email,
            password="TestPassword123!",
        )

        original_refresh_token = original_tokens.refresh_token

        rotated_tokens = AuthService.refresh_access_token(
            db=db,
            refresh_token=original_refresh_token,
        )

        assert rotated_tokens.access_token
        assert rotated_tokens.refresh_token
        assert rotated_tokens.token_type == "bearer"

        assert (
            rotated_tokens.refresh_token
            != original_refresh_token
        )

        original_record = (
            db.query(RefreshToken)
            .filter(
                RefreshToken.token_hash
                == TokenService.hash_refresh_token(
                    original_refresh_token
                )
            )
            .first()
        )

        assert original_record is not None
        assert original_record.revoked_at is not None

        new_record = (
            db.query(RefreshToken)
            .filter(
                RefreshToken.token_hash
                == TokenService.hash_refresh_token(
                    rotated_tokens.refresh_token
                )
            )
            .first()
        )

        assert new_record is not None
        assert new_record.user_id == user.id
        assert new_record.revoked_at is None

    finally:
        cleanup_user(db, email)


def test_refresh_access_token_rejects_reused_refresh_token(db):
    email = unique_email()

    try:
        request = UserRegisterRequest(
            email=email,
            password="TestPassword123!",
        )

        AuthService.register_user(
            db=db,
            request=request,
        )

        tokens = AuthService.login(
            db=db,
            email=email,
            password="TestPassword123!",
        )

        AuthService.refresh_access_token(
            db=db,
            refresh_token=tokens.refresh_token,
        )

        with pytest.raises(
            ValueError,
            match="Refresh token has been revoked",
        ):
            AuthService.refresh_access_token(
                db=db,
                refresh_token=tokens.refresh_token,
            )

    finally:
        cleanup_user(db, email)


def test_refresh_access_token_rejects_invalid_refresh_token(db):
    with pytest.raises(
        ValueError,
        match="Invalid refresh token",
    ):
        AuthService.refresh_access_token(
            db=db,
            refresh_token="invalid-refresh-token",
        )


def test_refresh_access_token_rejects_expired_refresh_token(db):
    email = unique_email()

    try:
        request = UserRegisterRequest(
            email=email,
            password="TestPassword123!",
        )

        user = AuthService.register_user(
            db=db,
            request=request,
        )

        refresh_token = TokenService.create_refresh_token()

        expired_record = RefreshToken(
            user_id=user.id,
            token_hash=TokenService.hash_refresh_token(
                refresh_token
            ),
            expires_at=(
                datetime.now(timezone.utc)
                - timedelta(minutes=1)
            ),
        )

        db.add(expired_record)
        db.commit()

        with pytest.raises(
            ValueError,
            match="Refresh token has expired",
        ):
            AuthService.refresh_access_token(
                db=db,
                refresh_token=refresh_token,
            )

    finally:
        cleanup_user(db, email)