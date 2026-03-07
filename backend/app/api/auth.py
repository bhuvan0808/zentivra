"""Authentication API endpoints (signup, login, logout, me)."""

from fastapi import APIRouter, Depends, Header

from app.dependencies import get_auth_service, get_current_user, get_current_user_full, CurrentUser
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    SignupRequest,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup", response_model=AuthResponse, status_code=201)
async def signup(
    body: SignupRequest,
    service: AuthService = Depends(get_auth_service),
):
    return await service.signup(
        body.username, body.email, body.password, body.display_name
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    body: LoginRequest,
    service: AuthService = Depends(get_auth_service),
):
    return await service.login(body.username, body.password)


@router.post("/logout")
async def logout(
    authorization: str = Header(..., alias="Authorization"),
    _user: CurrentUser = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    token = authorization.removeprefix("Bearer ").strip()
    if token:
        await service.logout(token)
    return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user_full)):
    return current_user
