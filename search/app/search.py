"""Full-text search over the corpus using Postgres FTS."""
from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Article, ArticleContent, ArticleTag, Tag

HEADLINE_OPTS = (
    "StartSel=<mark>, StopSel=</mark>, MaxFragments=2, "
    "FragmentDelimiter= … , MinWords=8, MaxWords=30"
)


async def search(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    query: str,
    tags: list[str] | None = None,
    limit: int = 20,
) -> dict:
    tsquery = func.websearch_to_tsquery("english", query)
    rank = func.ts_rank(ArticleContent.search_vector, tsquery).label("rank")
    snippet = func.ts_headline(
        "english", ArticleContent.content_text, tsquery, HEADLINE_OPTS
    ).label("snippet")

    stmt = (
        select(
            Article.id,
            Article.url,
            Article.title,
            Article.excerpt,
            Article.lead_image_url,
            Article.reading_minutes,
            rank,
            snippet,
        )
        .join(ArticleContent, ArticleContent.article_id == Article.id)
        .where(
            Article.user_id == user_id,
            ArticleContent.search_vector.op("@@")(tsquery),
        )
        .order_by(rank.desc())
        .limit(limit)
    )

    if tags:
        stmt = (
            stmt.join(ArticleTag, ArticleTag.article_id == Article.id)
            .join(Tag, Tag.id == ArticleTag.tag_id)
            .where(Tag.name.in_(tags))
            .distinct()
        )

    rows = (await session.execute(stmt)).all()

    article_ids = [r.id for r in rows]
    tags_by_article: dict[uuid.UUID, list[str]] = {}
    if article_ids:
        tag_rows = await session.execute(
            select(ArticleTag.article_id, Tag.name)
            .join(Tag, Tag.id == ArticleTag.tag_id)
            .where(ArticleTag.article_id.in_(article_ids))
        )
        for article_id, name in tag_rows.all():
            tags_by_article.setdefault(article_id, []).append(name)

    results = [
        {
            "id": str(r.id),
            "url": r.url,
            "title": r.title,
            "excerpt": r.excerpt,
            "lead_image_url": r.lead_image_url,
            "reading_minutes": r.reading_minutes,
            "snippet": r.snippet,
            "rank": float(r.rank),
            "tags": tags_by_article.get(r.id, []),
        }
        for r in rows
    ]
    return {"query": query, "total": len(results), "results": results}
