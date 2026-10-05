from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)


# ============================================================
# USER REGISTRATION
# ============================================================


class UserRegisterRequest(BaseModel):
    """
    Payload used to register a new platform member.

    The platform generates the unique user_id on the backend.
    The client must never supply or modify it.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    first_name: str = Field(
        min_length=2,
        max_length=100,
    )

    last_name: str = Field(
        min_length=1,
        max_length=100,
    )

    email: EmailStr

    mobile_number: str = Field(
        min_length=10,
        max_length=10,
    )

    password: str = Field(
        min_length=8,
        max_length=128,
    )

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """
        Allow alphabetic names with spaces, apostrophes,
        and hyphens.

        Examples:
            Revanth
            Mary Jane
            O'Connor
            Anne-Marie
        """

        value = value.strip()

        if not value:
            raise ValueError("Name cannot be empty")

        if not all(
            character.isalpha()
            or character in {" ", "'", "-"}
            for character in value
        ):
            raise ValueError(
                "Name may contain only letters, spaces, "
                "apostrophes, and hyphens"
            )

        if not any(character.isalpha() for character in value):
            raise ValueError("Name must contain letters")

        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> EmailStr:
        """
        Normalize email casing before it reaches the service layer.
        """

        return EmailStr(str(value).strip().lower())

    @field_validator("mobile_number")
    @classmethod
    def validate_mobile_number(cls, value: str) -> str:
        """
        Require a ten-digit mobile number.

        The database stores the normalized numeric value.
        """

        value = value.strip()

        if not value.isdigit():
            raise ValueError(
                "Mobile number must contain digits only"
            )

        if len(value) != 10:
            raise ValueError(
                "Mobile number must contain exactly 10 digits"
            )

        if value[0] not in "6789":
            raise ValueError(
                "Mobile number must start with 6, 7, 8, or 9"
            )

        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        """
        Basic password requirements.

        Password hashing is handled by the authentication service;
        plaintext passwords are never persisted.
        """

        if value.strip() != value:
            raise ValueError(
                "Password must not start or end with whitespace"
            )

        if len(value) < 8:
            raise ValueError(
                "Password must contain at least 8 characters"
            )

        if not any(character.isalpha() for character in value):
            raise ValueError(
                "Password must contain at least one letter"
            )

        if not any(character.isdigit() for character in value):
            raise ValueError(
                "Password must contain at least one digit"
            )

        return value


# ============================================================
# USER LOGIN
# ============================================================


class UserLoginRequest(BaseModel):
    """
    Payload used to authenticate an existing member.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    email: EmailStr

    password: str = Field(
        min_length=1,
        max_length=128,
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> EmailStr:
        return EmailStr(str(value).strip().lower())


# ============================================================
# REFRESH TOKEN
# ============================================================


class RefreshTokenRequest(BaseModel):
    """
    Payload used to rotate a refresh token.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    refresh_token: str = Field(
        min_length=1,
        max_length=512,
    )


# ============================================================
# TOKEN RESPONSE
# ============================================================


class TokenResponse(BaseModel):
    """
    Authentication token pair returned after login or refresh.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    token_type: str = "bearer"

    access_token: str

    refresh_token: str

    expires_in: int = Field(
        gt=0,
    )


# ============================================================
# USER RESPONSE
# ============================================================


class UserResponse(BaseModel):
    """
    Public representation of an authenticated platform member.

    The password hash is intentionally never exposed.
    """

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    id: UUID

    user_id: str

    first_name: str

    last_name: str

    email: EmailStr

    mobile_number: str

    is_active: bool

    created_at: datetime

    updated_at: datetime