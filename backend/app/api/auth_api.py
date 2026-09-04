from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.auth_schemas import (
    RefreshTokenRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from backend.app.services.auth_service import AuthService


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    request: UserRegisterRequest,
    db: Session = Depends(get_db),
) -> UserResponse:
    """Register a new application user."""

    try:
        return AuthService.register_user(
            db=db,
            request=request,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
def login_user(
    request: UserLoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Authenticate a user and return an access/refresh token pair."""

    try:
        return AuthService.login(
            db=db,
            email=str(request.email),
            password=request.password,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
def refresh_access_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Rotate a refresh token and issue a new token pair."""

    try:
        return AuthService.refresh_access_token(
            db=db,
            refresh_token=request.refresh_token,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc