from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    hash_password,
    verify_password,
)

from backend.app.models.refresh_token_model import RefreshToken
from backend.app.models.user_model import User
from backend.app.schemas.auth_schemas import (
    TokenResponse,
    UserRegisterRequest,
)
from backend.app.services.token_service import TokenService


class AuthService:
    """Authentication business logic."""

    @staticmethod
    def register_user(
        db: Session,
        request: UserRegisterRequest,
    ) -> User:
        """
        Create a new application user.

        Raises:
            ValueError: If the email is already registered.
        """

        email = str(request.email).lower()

        existing_user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

        if existing_user is not None:
            raise ValueError("Email is already registered")

        user = User(
            email=email,
            password_hash=hash_password(request.password),
            is_active=True,
        )

        db.add(user)

        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise ValueError(
                "Email is already registered"
            ) from exc

        db.refresh(user)

        return user

    @staticmethod
    def authenticate_user(
        db: Session,
        email: str,
        password: str,
    ) -> User | None:
        """
        Authenticate a user using email and password.

        Returns:
            Authenticated User when credentials are valid,
            otherwise None.
        """

        normalized_email = email.lower()

        user = (
            db.query(User)
            .filter(User.email == normalized_email)
            .first()
        )

        if user is None:
            return None

        if not user.is_active:
            return None

        if not verify_password(
            password,
            user.password_hash,
        ):
            return None

        return user

    @staticmethod
    def create_token_pair(
        db: Session,
        user: User,
    ) -> TokenResponse:
        """
        Create an access-token and refresh-token pair.

        The raw refresh token is returned to the caller.
        Only its SHA-256 hash is persisted.
        """

        access_token = TokenService.create_access_token(
            user.id
        )

        refresh_token = TokenService.create_refresh_token()

        refresh_token_record = RefreshToken(
            user_id=user.id,
            token_hash=TokenService.hash_refresh_token(
                refresh_token
            ),
            expires_at=TokenService.get_refresh_token_expiry(),
        )

        db.add(refresh_token_record)

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    @staticmethod
    def login(
        db: Session,
        email: str,
        password: str,
    ) -> TokenResponse:
        """
        Authenticate a user and create a token pair.

        Raises:
            ValueError: If credentials are invalid.
        """

        user = AuthService.authenticate_user(
            db=db,
            email=email,
            password=password,
        )

        if user is None:
            raise ValueError("Invalid email or password")

        return AuthService.create_token_pair(
            db=db,
            user=user,
        )

    @staticmethod
    def refresh_access_token(
        db: Session,
        refresh_token: str,
    ) -> TokenResponse:
        """
        Rotate a refresh token and issue a new token pair.

        The existing refresh token is revoked before the
        replacement token is persisted.
        """

        token_hash = TokenService.hash_refresh_token(
            refresh_token
        )

        stored_token = (
            db.query(RefreshToken)
            .filter(
                RefreshToken.token_hash == token_hash
            )
            .first()
        )

        if stored_token is None:
            raise ValueError("Invalid refresh token")

        now = datetime.now(timezone.utc)

        if stored_token.revoked_at is not None:
            raise ValueError("Refresh token has been revoked")

        if stored_token.expires_at <= now:
            raise ValueError("Refresh token has expired")

        user = (
            db.query(User)
            .filter(User.id == stored_token.user_id)
            .first()
        )

        if user is None or not user.is_active:
            raise ValueError("User is inactive or does not exist")

        # Revoke the old refresh token.
        stored_token.revoked_at = now

        # Create the replacement token.
        new_access_token = TokenService.create_access_token(
            user.id
        )

        new_refresh_token = TokenService.create_refresh_token()

        new_refresh_token_record = RefreshToken(
            user_id=user.id,
            token_hash=TokenService.hash_refresh_token(
                new_refresh_token
            ),
            expires_at=TokenService.get_refresh_token_expiry(),
        )

        db.add(new_refresh_token_record)

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )