from datetime import datetime, timezone
from secrets import token_hex

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.security import hash_password, verify_password
from backend.app.models.refresh_token_model import RefreshToken
from backend.app.models.user_model import User
from backend.app.schemas.auth_schemas import (
    TokenResponse,
    UserRegisterRequest,
)
from backend.app.services.token_service import TokenService


class AuthService:
    """Authentication business logic."""

    # ============================================================
    # USER ID GENERATION
    # ============================================================

    @staticmethod
    def _generate_user_id(db: Session) -> str:
        """
        Generate a unique platform user ID.

        Format:
            USR-XXXXXXXXXX

        The generated identifier contains alphanumeric characters
        with a platform prefix and is persisted as the user's
        permanent platform identity.
        """

        for _ in range(10):
            user_id = f"USR-{token_hex(5).upper()}"

            existing_user = (
                db.query(User)
                .filter(User.user_id == user_id)
                .first()
            )

            if existing_user is None:
                return user_id

        raise RuntimeError(
            "Unable to generate a unique user ID"
        )

    # ============================================================
    # USER REGISTRATION
    # ============================================================

    @staticmethod
    def register_user(
        db: Session,
        request: UserRegisterRequest,
    ) -> User:
        """
        Register a new application member.

        Registration creates:
        - permanent platform user ID
        - first name
        - last name
        - email
        - mobile number
        - Argon2 password hash
        - active account

        User ID is generated exclusively by the backend.
        """

        email = str(request.email).strip().lower()
        mobile_number = request.mobile_number.strip()

        # --------------------------------------------------------
        # EMAIL UNIQUENESS
        # --------------------------------------------------------

        existing_email = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

        if existing_email is not None:
            raise ValueError(
                "Email is already registered"
            )

        # --------------------------------------------------------
        # MOBILE UNIQUENESS
        # --------------------------------------------------------

        existing_mobile = (
            db.query(User)
            .filter(
                User.mobile_number == mobile_number
            )
            .first()
        )

        if existing_mobile is not None:
            raise ValueError(
                "Mobile number is already registered"
            )

        # --------------------------------------------------------
        # GENERATE PLATFORM USER ID
        # --------------------------------------------------------

        user_id = AuthService._generate_user_id(db)

        # --------------------------------------------------------
        # CREATE USER
        # --------------------------------------------------------

        user = User(
            user_id=user_id,
            first_name=request.first_name.strip(),
            last_name=request.last_name.strip(),
            email=email,
            mobile_number=mobile_number,
            password_hash=hash_password(
                request.password
            ),
            is_active=True,
        )

        db.add(user)

        try:
            db.commit()

        except IntegrityError as exc:
            db.rollback()

            # Re-check unique fields after a possible
            # concurrent registration.
            email_exists = (
                db.query(User)
                .filter(User.email == email)
                .first()
            )

            if email_exists is not None:
                raise ValueError(
                    "Email is already registered"
                ) from exc

            mobile_exists = (
                db.query(User)
                .filter(
                    User.mobile_number == mobile_number
                )
                .first()
            )

            if mobile_exists is not None:
                raise ValueError(
                    "Mobile number is already registered"
                ) from exc

            raise

        db.refresh(user)

        return user

    # ============================================================
    # USER AUTHENTICATION
    # ============================================================

    @staticmethod
    def authenticate_user(
        db: Session,
        email: str,
        password: str,
    ) -> User | None:
        """
        Authenticate an existing user using email and password.

        Returns:
            Authenticated User when credentials are valid.
            None when credentials are invalid.
        """

        normalized_email = (
            email.strip().lower()
        )

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

    # ============================================================
    # TOKEN PAIR
    # ============================================================

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

        access_token = (
            TokenService.create_access_token(
                user.id
            )
        )

        refresh_token = (
            TokenService.create_refresh_token()
        )

        refresh_token_record = RefreshToken(
            user_id=user.id,
            token_hash=TokenService.hash_refresh_token(
                refresh_token
            ),
            expires_at=(
                TokenService.get_refresh_token_expiry()
            ),
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
            expires_in=(
                settings.ACCESS_TOKEN_EXPIRE_MINUTES
                * 60
            ),
        )

    # ============================================================
    # LOGIN
    # ============================================================

    @staticmethod
    def login(
        db: Session,
        email: str,
        password: str,
    ) -> TokenResponse:
        """
        Authenticate a user and create a token pair.

        Raises:
            ValueError:
                When credentials are invalid.
        """

        user = AuthService.authenticate_user(
            db=db,
            email=email,
            password=password,
        )

        if user is None:
            raise ValueError(
                "Invalid email or password"
            )

        return AuthService.create_token_pair(
            db=db,
            user=user,
        )

    # ============================================================
    # REFRESH TOKEN ROTATION
    # ============================================================

    @staticmethod
    def refresh_access_token(
        db: Session,
        refresh_token: str,
    ) -> TokenResponse:
        """
        Rotate a refresh token and issue a new
        access-token / refresh-token pair.

        The previous refresh token is revoked and
        cannot be reused.
        """

        token_hash = (
            TokenService.hash_refresh_token(
                refresh_token
            )
        )

        stored_token = (
            db.query(RefreshToken)
            .filter(
                RefreshToken.token_hash
                == token_hash
            )
            .first()
        )

        if stored_token is None:
            raise ValueError(
                "Invalid refresh token"
            )

        now = datetime.now(timezone.utc)

        if stored_token.revoked_at is not None:
            raise ValueError(
                "Refresh token has been revoked"
            )

        if stored_token.expires_at <= now:
            raise ValueError(
                "Refresh token has expired"
            )

        user = (
            db.query(User)
            .filter(
                User.id == stored_token.user_id
            )
            .first()
        )

        if user is None or not user.is_active:
            raise ValueError(
                "User is inactive or does not exist"
            )

        # --------------------------------------------------------
        # REVOKE OLD REFRESH TOKEN
        # --------------------------------------------------------

        stored_token.revoked_at = now

        # --------------------------------------------------------
        # CREATE NEW ACCESS TOKEN
        # --------------------------------------------------------

        new_access_token = (
            TokenService.create_access_token(
                user.id
            )
        )

        # --------------------------------------------------------
        # CREATE NEW REFRESH TOKEN
        # --------------------------------------------------------

        new_refresh_token = (
            TokenService.create_refresh_token()
        )

        new_refresh_token_record = RefreshToken(
            user_id=user.id,
            token_hash=(
                TokenService.hash_refresh_token(
                    new_refresh_token
                )
            ),
            expires_at=(
                TokenService.get_refresh_token_expiry()
            ),
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
            expires_in=(
                settings.ACCESS_TOKEN_EXPIRE_MINUTES
                * 60
            ),
        )