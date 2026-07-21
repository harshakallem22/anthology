"""Auth router: Google OAuth 2.0 / OIDC + a guarded local dev-login (spec §7)."""
from __future__ import annotations

import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..db import get_session
from ..models import User
from ..schemas import UserOut
from .security import create_session_token, current_user, upsert_user

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"

DEMO_EMAIL = "demo@anthology.local"


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.is_production,
        max_age=60 * 60 * 24 * 14,
        path="/",
    )


@router.get("/google/login")
async def google_login(request: Request) -> RedirectResponse:
    if not settings.google_oauth_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured. Use POST /auth/dev-login.",
        )
    state = secrets.token_urlsafe(16)
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    response = RedirectResponse(f"{GOOGLE_AUTH_URL}?{urlencode(params)}")
    response.set_cookie(
        "oauth_state", state, httponly=True, samesite="lax",
        secure=settings.is_production, max_age=600, path="/",
    )
    return response


@router.get("/google/callback")
async def google_callback(
    code: str,
    state: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    if not settings.google_oauth_enabled:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured.")
    if request.cookies.get("oauth_state") != state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    async with httpx.AsyncClient(timeout=15) as client:
        token_resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        token_resp.raise_for_status()
        access_token = token_resp.json()["access_token"]

        userinfo_resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        userinfo_resp.raise_for_status()
        profile = userinfo_resp.json()

    user = await upsert_user(
        session,
        email=profile["email"],
        google_sub=profile.get("sub"),
        display_name=profile.get("name"),
        avatar_url=profile.get("picture"),
    )
    token = create_session_token(user.id)
    response = RedirectResponse(settings.web_origin)
    _set_session_cookie(response, token)
    response.delete_cookie("oauth_state", path="/")
    return response


@router.post("/dev-login", response_model=UserOut)
async def dev_login(
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> User:
    """Sign in a seeded demo user. Development-only (guarded by ENV)."""
    if settings.is_production:
        raise HTTPException(status_code=404, detail="Not found")
    user = await upsert_user(
        session,
        email=DEMO_EMAIL,
        display_name="Demo Reader",
        avatar_url=None,
    )
    token = create_session_token(user.id)
    _set_session_cookie(response, token)
    return user


@router.post("/logout")
async def logout(response: Response) -> dict:
    response.delete_cookie(settings.cookie_name, path="/")
    return {"ok": True}


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(current_user)) -> User:
    return user
