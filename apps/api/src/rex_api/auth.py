"""Authentication router: magic links, session tokens, and user profile management."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from rex_shared.schemas import User, UserUpdate

router = APIRouter(prefix="/v1", tags=["auth"])

# In-memory user store for dev/testing (backed by DB when DATABASE_URL is active)
_USERS: dict[uuid.UUID, User] = {}
_USERS_BY_EMAIL: dict[str, uuid.UUID] = {}


def get_or_create_user(email: str, display_name: str = "") -> User:
    email_clean = email.lower().strip()
    if email_clean in _USERS_BY_EMAIL:
        return _USERS[_USERS_BY_EMAIL[email_clean]]

    # Generate deterministic UUID from email for consistent dev sessions
    user_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"rex.user.{email_clean}")
    user = User(
        id=user_id,
        email=email_clean,
        display_name=display_name or email_clean.split("@")[0].title(),
        preferred_lang="hi-IN",
        timezone="Asia/Kolkata",
        created_at=datetime.now(UTC),
    )
    _USERS[user_id] = user
    _USERS_BY_EMAIL[email_clean] = user_id
    return user


def create_token(payload: dict[str, Any], secret: str, expires_in_seconds: int, algorithm: str = "HS256") -> str:
    claims = {
        **payload,
        "exp": datetime.now(UTC) + timedelta(seconds=expires_in_seconds),
        "iat": datetime.now(UTC),
    }
    return jwt.encode(claims, secret, algorithm=algorithm)


def decode_token(token: str, secret: str, algorithm: str = "HS256") -> dict[str, Any]:
    try:
        return jwt.decode(token, secret, algorithms=[algorithm])
    except jwt.ExpiredSignatureError as err:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired") from err
    except jwt.InvalidTokenError as err:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from err


class MagicLinkRequest(BaseModel):
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class MagicLinkResponse(BaseModel):
    message: str
    debug_token: str | None = None


class CallbackResponse(BaseModel):
    session_token: str
    user: User


async def get_current_user(request: Request, authorization: str | None = Header(default=None)) -> User:
    settings = request.app.state.settings
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1].strip()
        claims = decode_token(token, settings.session_secret, settings.jwt_algorithm)
        if claims.get("type") != "session":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        user_id = uuid.UUID(claims["sub"])
        if user_id not in _USERS:
            # Recreate user from claims if present
            return get_or_create_user(claims.get("email", "user@example.com"))
        return _USERS[user_id]

    if settings.dev_auth:
        return get_or_create_user("dev@rex.internal", display_name="Dev User")
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")


@router.post("/auth/magic-link", response_model=MagicLinkResponse, status_code=status.HTTP_202_ACCEPTED)
async def request_magic_link(body: MagicLinkRequest, request: Request) -> MagicLinkResponse:
    settings = request.app.state.settings
    user = get_or_create_user(body.email)
    token = create_token(
        {"sub": str(user.id), "email": user.email, "type": "magic_link"},
        settings.session_secret,
        settings.magic_link_ttl_s,
        settings.jwt_algorithm,
    )
    return MagicLinkResponse(
        message=f"Magic link sent to {body.email}",
        debug_token=token if settings.dev_auth else None,
    )


@router.get("/auth/callback", response_model=CallbackResponse)
async def auth_callback(token: str, request: Request, response: Response) -> CallbackResponse:
    settings = request.app.state.settings
    claims = decode_token(token, settings.session_secret, settings.jwt_algorithm)
    if claims.get("type") != "magic_link":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Expected magic_link token")

    user_id = uuid.UUID(claims["sub"])
    user = _USERS.get(user_id) or get_or_create_user(claims.get("email", "user@example.com"))

    session_token = create_token(
        {"sub": str(user.id), "email": user.email, "type": "session"},
        settings.session_secret,
        settings.jwt_access_ttl_s,
        settings.jwt_algorithm,
    )
    # Set httpOnly cookie for web dashboard
    response.set_cookie(
        key="rex_session",
        value=session_token,
        max_age=settings.jwt_access_ttl_s,
        httponly=True,
        samesite="lax",
    )
    return CallbackResponse(session_token=session_token, user=user)


@router.get("/me", response_model=User)
async def get_me(user: Annotated[User, Depends(get_current_user)]) -> User:
    return user


@router.patch("/me", response_model=User)
async def update_me(update: UserUpdate, user: Annotated[User, Depends(get_current_user)]) -> User:
    user_data = user.model_dump()
    for field, val in update.model_dump(exclude_unset=True).items():
        if val is not None:
            user_data[field] = val
    updated_user = User(**user_data)
    _USERS[user.id] = updated_user
    return updated_user
