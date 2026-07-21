"""Article CRUD + tag attach/detach (spec §3.1)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..db import get_session
from ..models import Article, ArticleContent, ArticleTag, Tag, User
from ..schemas import ArticleDetail, ArticleOut, ArticleUpdate, TagOut
from ..auth.security import current_user

router = APIRouter(prefix="/articles", tags=["articles"])


async def _get_owned_article(
    article_id: uuid.UUID, user: User, session: AsyncSession
) -> Article:
    stmt = (
        select(Article)
        .where(Article.id == article_id, Article.user_id == user.id)
        .options(selectinload(Article.tags))
    )
    article = (await session.execute(stmt)).scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.get("", response_model=list[ArticleOut])
async def list_articles(
    archived: bool = Query(False, description="Show archived instead of active"),
    favorite: bool | None = Query(None),
    tag: str | None = Query(None, description="Filter by tag name"),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> list[Article]:
    stmt = (
        select(Article)
        .where(Article.user_id == user.id, Article.is_archived == archived)
        .options(selectinload(Article.tags))
        .order_by(Article.saved_at.desc().nullslast(), Article.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if favorite is not None:
        stmt = stmt.where(Article.is_favorite == favorite)
    if tag:
        stmt = stmt.join(Article.tags).where(Tag.name == tag)
    return list((await session.execute(stmt)).scalars().all())


@router.get("/{article_id}", response_model=ArticleDetail)
async def get_article(
    article_id: uuid.UUID,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> ArticleDetail:
    article = await _get_owned_article(article_id, user, session)
    content = await session.get(ArticleContent, article.id)
    detail = ArticleDetail.model_validate(article)
    if content:
        detail.content_html = content.content_html
        detail.content_text = content.content_text
    return detail


@router.patch("/{article_id}", response_model=ArticleOut)
async def update_article(
    article_id: uuid.UUID,
    payload: ArticleUpdate,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> Article:
    article = await _get_owned_article(article_id, user, session)
    if payload.is_archived is not None:
        article.is_archived = payload.is_archived
    if payload.is_favorite is not None:
        article.is_favorite = payload.is_favorite
    await session.commit()
    await session.refresh(article, attribute_names=["tags"])
    return article


@router.delete("/{article_id}", status_code=204, response_model=None)
async def delete_article(
    article_id: uuid.UUID,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    article = await _get_owned_article(article_id, user, session)
    await session.delete(article)
    await session.commit()


@router.post("/{article_id}/tags", response_model=list[TagOut])
async def add_tag(
    article_id: uuid.UUID,
    payload: dict,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> list[Tag]:
    name = (payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=422, detail="Tag name is required")
    article = await _get_owned_article(article_id, user, session)

    tag = (
        await session.execute(
            select(Tag).where(Tag.user_id == user.id, Tag.name == name)
        )
    ).scalar_one_or_none()
    if tag is None:
        tag = Tag(user_id=user.id, name=name)
        session.add(tag)
        await session.flush()
    if tag not in article.tags:
        article.tags.append(tag)
    await session.commit()
    await session.refresh(article, attribute_names=["tags"])
    return article.tags


@router.delete("/{article_id}/tags/{tag_name}", response_model=list[TagOut])
async def remove_tag(
    article_id: uuid.UUID,
    tag_name: str,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> list[Tag]:
    article = await _get_owned_article(article_id, user, session)
    tag = (
        await session.execute(
            select(Tag).where(Tag.user_id == user.id, Tag.name == tag_name)
        )
    ).scalar_one_or_none()
    if tag:
        await session.execute(
            delete(ArticleTag).where(
                ArticleTag.article_id == article.id, ArticleTag.tag_id == tag.id
            )
        )
        await session.commit()
        await session.refresh(article, attribute_names=["tags"])
    return article.tags
