"""
Pydantic schemas for authentication endpoints.

Defines request and response schemas for:
- POST /auth/signup: SignupRequest -> AuthResponse
- POST /auth/login: LoginRequest -> AuthResponse
- GET /auth/me: UserResponse (current user profile)
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SignupRequest(BaseModel):
    """Request body for user registration (POST /auth/signup)."""

    username: str = Field(..., min_length=3, max_length=100)
    email: str = Field(
        ..., max_length=255, pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    )
    password: str = Field(..., min_length=6)
    display_name: str = Field(..., min_length=1, max_length=150)


class LoginRequest(BaseModel):
    username: str = Field(..., description="Accepts username or email")
    password: str


class AuthResponse(BaseModel):
    user_id: str
    username: str
    email: str
    display_name: str
    auth_token: str
    expires_at: datetime


class UserResponse(BaseModel):
    """Response for current user profile (GET /auth/me). Exposes user info without auth token."""

    user_id: str
    username: str
    email: str
    display_name: str
    created_at: datetime

    model_config = {"from_attributes": True}
