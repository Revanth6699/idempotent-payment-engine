from datetime import datetime, timedelta, timezone
from hashlib import sha256
from secrets import token_urlsafe
from uuid import UUID

from jose import JWTError, jwt

from backend.app.core.config import settings


class TokenService:
    """Create, decode, and hash authentication tokens."""

    JWT_ALGORITHM = "HS256"
    JWT_SECRET_KEY = settings.SECRET_KEY
    ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    ACCESS_TOKEN_TYPE = "access"
    REFRESH_TOKEN_TYPE = "refresh"

    REFRESH_TOKEN_EXPIRE_DAYS = 7

    @staticmethod
    def create_access_token(user_id: UUID) -> str:
        """
        Create a short-lived JWT access token for a user.
        """

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(
            minutes=TokenService.ACCESS_TOKEN_EXPIRE_MINUTES
        )

        payload = {
            "sub": str(user_id),
            "type": TokenService.ACCESS_TOKEN_TYPE,
            "iat": now,
            "exp": expires_at,
        }

        return jwt.encode(
            payload,
            TokenService.JWT_SECRET_KEY,
            algorithm=TokenService.JWT_ALGORITHM,
        )

    @staticmethod
    def create_refresh_token() -> str:
        """
        Create an opaque refresh token.

        The raw token is returned once to the caller.
        Only its hash will be persisted in the database.
        """

        return token_urlsafe(48)

    @staticmethod
    def hash_refresh_token(refresh_token: str) -> str:
        """
        Create a SHA-256 hash of a refresh token for persistence.
        """

        return sha256(
            refresh_token.encode("utf-8")
        ).hexdigest()

    @staticmethod
    def get_refresh_token_expiry() -> datetime:
        """
        Return the expiration timestamp for a refresh token.
        """

        return datetime.now(timezone.utc) + timedelta(
            days=TokenService.REFRESH_TOKEN_EXPIRE_DAYS
        )

    @staticmethod
    def decode_access_token(token: str) -> UUID:
        """
        Decode and validate a JWT access token.

        Raises:
            ValueError: If the token is invalid, expired,
            or is not an access token.
        """

        try:
            payload = jwt.decode(
                token,
                TokenService.JWT_SECRET_KEY,
                algorithms=[TokenService.JWT_ALGORITHM],
            )
        except JWTError as exc:
            raise ValueError("Invalid or expired access token") from exc

        if payload.get("type") != TokenService.ACCESS_TOKEN_TYPE:
            raise ValueError("Invalid access token type")

        subject = payload.get("sub")

        if not subject:
            raise ValueError("Access token subject is missing")

        try:
            return UUID(subject)
        except (ValueError, TypeError) as exc:
            raise ValueError("Invalid access token subject") from exc