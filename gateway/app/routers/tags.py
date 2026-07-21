"""Per-user tag listing (used for library filter chips)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.security import current_user
from ..db import get_session
from ..models import Tag, User
from ..schemas import TagOut

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=list[TagOut])
async def list_tags(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> list[Tag]:
    stmt = select(Tag).where(Tag.user_id == user.id).order_by(Tag.name)
    return list((await session.execute(stmt)).scalars().all())
