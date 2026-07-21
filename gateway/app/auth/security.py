"""JWT session helpers and the current_user dependency."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..db import get_session
from ..models import User

settings = get_settings()

ALGORITHM = "HS256"
SESSION_TTL = timedelta(days=14)


def create_session_token(user_id: uuid.UUID) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + SESSION_TTL,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_session_token(token: str) -> uuid.UUID:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        return uuid.UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session"
        ) from exc


async def current_user(
    anthology_session: str | None = Cookie(default=None),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Resolve the authenticated user from the session cookie."""
    if not anthology_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    user_id = decode_session_token(anthology_session)
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return user


async def upsert_user(
    session: AsyncSession,
    *,
    email: str,
    google_sub: str | None = None,
    display_name: str | None = None,
    avatar_url: str | None = None,
) -> User:
    """Create or update a user from an OIDC profile (or the dev seed)."""
    stmt = select(User).where(User.email == email)
    user = (await session.execute(stmt)).scalar_one_or_none()
    if user is None:
        user = User(
            email=email,
            google_sub=google_sub,
            display_name=display_name,
            avatar_url=avatar_url,
        )
        session.add(user)
    else:
        user.google_sub = google_sub or user.google_sub
        user.display_name = display_name or user.display_name
        user.avatar_url = avatar_url or user.avatar_url
    await session.commit()
    await session.refresh(user)
    return user
