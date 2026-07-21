"""Highlight creation/listing/deletion (spec §5.7)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.security import current_user
from ..db import get_session
from ..models import Article, Highlight, User
from ..schemas import HighlightCreate, HighlightOut

router = APIRouter(tags=["highlights"])


async def _assert_owns_article(
    article_id: uuid.UUID, user: User, session: AsyncSession
) -> None:
    stmt = select(Article.id).where(
        Article.id == article_id, Article.user_id == user.id
    )
    if (await session.execute(stmt)).scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Article not found")


@router.post("/articles/{article_id}/highlights", response_model=HighlightOut, status_code=201)
async def create_highlight(
    article_id: uuid.UUID,
    payload: HighlightCreate,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> Highlight:
    await _assert_owns_article(article_id, user, session)
    highlight = Highlight(
        user_id=user.id,
        article_id=article_id,
        quote=payload.quote,
        note=payload.note,
        position=payload.position,
    )
    session.add(highlight)
    await session.commit()
    await session.refresh(highlight)
    return highlight


@router.get("/articles/{article_id}/highlights", response_model=list[HighlightOut])
async def list_highlights(
    article_id: uuid.UUID,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> list[Highlight]:
    await _assert_owns_article(article_id, user, session)
    stmt = (
        select(Highlight)
        .where(Highlight.article_id == article_id, Highlight.user_id == user.id)
        .order_by(Highlight.created_at)
    )
    return list((await session.execute(stmt)).scalars().all())


@router.delete("/highlights/{highlight_id}", status_code=204, response_model=None)
async def delete_highlight(
    highlight_id: uuid.UUID,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    highlight = await session.get(Highlight, highlight_id)
    if highlight is None or highlight.user_id != user.id:
        raise HTTPException(status_code=404, detail="Highlight not found")
    await session.delete(highlight)
    await session.commit()
