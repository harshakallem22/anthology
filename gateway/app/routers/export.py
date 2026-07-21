"""Export the user's whole library as JSON - the anti-lock-in feature (spec §5.9)."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..auth.security import current_user
from ..db import get_session
from ..models import Article, ArticleContent, Highlight, User

router = APIRouter(tags=["export"])


@router.get("/export")
async def export_library(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    articles = (
        await session.execute(
            select(Article)
            .where(Article.user_id == user.id)
            .options(selectinload(Article.tags))
            .order_by(Article.created_at)
        )
    ).scalars().all()

    highlights = (
        await session.execute(
            select(Highlight).where(Highlight.user_id == user.id)
        )
    ).scalars().all()
    highlights_by_article: dict = {}
    for h in highlights:
        highlights_by_article.setdefault(str(h.article_id), []).append(
            {
                "quote": h.quote,
                "note": h.note,
                "position": h.position,
                "created_at": h.created_at.isoformat() if h.created_at else None,
            }
        )

    items = []
    for a in articles:
        content = await session.get(ArticleContent, a.id)
        items.append(
            {
                "url": a.url,
                "title": a.title,
                "byline": a.byline,
                "excerpt": a.excerpt,
                "lead_image_url": a.lead_image_url,
                "word_count": a.word_count,
                "reading_minutes": a.reading_minutes,
                "saved_at": a.saved_at.isoformat() if a.saved_at else None,
                "is_archived": a.is_archived,
                "is_favorite": a.is_favorite,
                "extraction_status": a.extraction_status,
                "tags": [t.name for t in a.tags],
                "content_text": content.content_text if content else None,
                "highlights": highlights_by_article.get(str(a.id), []),
            }
        )

    payload = {
        "anthology_export_version": 1,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "user": {"email": user.email, "display_name": user.display_name},
        "article_count": len(items),
        "articles": items,
    }
    return JSONResponse(
        content=payload,
        headers={
            "Content-Disposition": 'attachment; filename="anthology-export.json"'
        },
    )
