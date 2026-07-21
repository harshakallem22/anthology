"""Extraction worker: parses imports, fetches URLs, extracts readable text."""
from __future__ import annotations

import base64
import uuid

from fastapi import BackgroundTasks, FastAPI
from pydantic import BaseModel
from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from .db import SessionLocal
from .extractor import Extracted, fetch_and_extract
from .importers import instapaper, pocket
from .importers.base import ParsedArticle
from .models import Article, ArticleContent, ArticleTag, Import, Tag

app = FastAPI(title="Anthology Extraction Worker", version="1.0.0")


class ExtractRequest(BaseModel):
    articleId: uuid.UUID
    url: str


class BatchRequest(BaseModel):
    importId: uuid.UUID


class IngestRequest(BaseModel):
    importId: uuid.UUID
    userId: uuid.UUID
    source: str
    filename: str | None = None
    fileContentBase64: str


async def _write_extraction(
    session: AsyncSession, article: Article, result: Extracted
) -> None:
    """Persist an extraction result, writing article metadata before content
    so the tsvector trigger reads the fresh title."""
    if not result.ok:
        article.extraction_status = "failed"
        await session.commit()
        return

    article.title = result.title or article.title
    article.byline = result.byline or article.byline
    article.lead_image_url = result.lead_image_url or article.lead_image_url
    article.excerpt = result.excerpt or article.excerpt
    article.word_count = result.word_count
    article.reading_minutes = result.reading_minutes
    article.extraction_status = "extracted"
    await session.flush()

    content = await session.get(ArticleContent, article.id)
    if content is None:
        content = ArticleContent(article_id=article.id)
        session.add(content)
    content.content_html = result.content_html
    content.content_text = result.content_text
    content.extracted_at = func.now()
    await session.commit()


async def _extract_one(session: AsyncSession, article: Article) -> str:
    result = await fetch_and_extract(article.url)
    await _write_extraction(session, article, result)
    return article.extraction_status


def _parse_file(source: str, raw: bytes) -> list[ParsedArticle]:
    if source == "pocket":
        return pocket.parse(raw)
    if source == "instapaper":
        return instapaper.parse(raw)
    raise ValueError(f"Unknown import source: {source}")


async def _get_or_create_tag(
    session: AsyncSession, user_id: uuid.UUID, name: str, cache: dict[str, uuid.UUID]
) -> uuid.UUID:
    if name in cache:
        return cache[name]
    stmt = pg_insert(Tag).values(id=uuid.uuid4(), user_id=user_id, name=name)
    stmt = stmt.on_conflict_do_nothing(index_elements=["user_id", "name"])
    await session.execute(stmt)
    tag_id = (
        await session.execute(
            select(Tag.id).where(Tag.user_id == user_id, Tag.name == name)
        )
    ).scalar_one()
    cache[name] = tag_id
    return tag_id


async def run_ingest(
    import_id: uuid.UUID, user_id: uuid.UUID, source: str, raw: bytes
) -> None:
    """Parse the export, create article rows, then extract each one."""
    async with SessionLocal() as session:
        try:
            parsed = _parse_file(source, raw)
        except ValueError:
            await session.execute(
                update(Import).where(Import.id == import_id).values(status="failed")
            )
            await session.commit()
            return

        tag_cache: dict[str, uuid.UUID] = {}
        created_ids: list[uuid.UUID] = []

        for item in parsed:
            new_id = uuid.uuid4()
            stmt = (
                pg_insert(Article)
                .values(
                    id=new_id,
                    user_id=user_id,
                    import_id=import_id,
                    url=item.url,
                    title=item.title,
                    excerpt=item.excerpt,
                    saved_at=item.saved_at,
                    is_archived=item.is_archived,
                    is_favorite=item.is_favorite,
                    extraction_status="pending",
                )
                .on_conflict_do_nothing(index_elements=["user_id", "url"])
                .returning(Article.id)
            )
            returned = (await session.execute(stmt)).scalar_one_or_none()
            if returned is None:
                continue
            created_ids.append(returned)

            for tag_name in item.tags:
                tag_id = await _get_or_create_tag(session, user_id, tag_name, tag_cache)
                await session.execute(
                    pg_insert(ArticleTag)
                    .values(article_id=returned, tag_id=tag_id)
                    .on_conflict_do_nothing()
                )

        await session.execute(
            update(Import)
            .where(Import.id == import_id)
            .values(total_count=len(created_ids), processed_count=0, status="processing")
        )
        await session.commit()

    for article_id in created_ids:
        async with SessionLocal() as session:
            article = await session.get(Article, article_id)
            if article is not None:
                try:
                    await _extract_one(session, article)
                except Exception:
                    article.extraction_status = "failed"
                    await session.commit()
            await session.execute(
                update(Import)
                .where(Import.id == import_id)
                .values(processed_count=Import.processed_count + 1)
            )
            await session.commit()

    async with SessionLocal() as session:
        await session.execute(
            update(Import).where(Import.id == import_id).values(status="complete")
        )
        await session.commit()


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "extraction"}


@app.post("/extract")
async def extract(req: ExtractRequest) -> dict:
    async with SessionLocal() as session:
        article = await session.get(Article, req.articleId)
        if article is None:
            return {"status": "not_found"}
        status = await _extract_one(session, article)
    return {"status": status}


@app.post("/extract/batch", status_code=202)
async def extract_batch(req: BatchRequest, background_tasks: BackgroundTasks) -> dict:
    background_tasks.add_task(_run_pending_batch, req.importId)
    return {"status": "processing", "importId": str(req.importId)}


async def _run_pending_batch(import_id: uuid.UUID) -> None:
    """Re-extract any pending articles for an existing import."""
    async with SessionLocal() as session:
        rows = (
            await session.execute(
                select(Article.id).where(
                    Article.import_id == import_id,
                    Article.extraction_status == "pending",
                )
            )
        ).scalars().all()
    for article_id in rows:
        async with SessionLocal() as session:
            article = await session.get(Article, article_id)
            if article is not None:
                try:
                    await _extract_one(session, article)
                except Exception:
                    article.extraction_status = "failed"
                    await session.commit()


@app.post("/imports/ingest", status_code=202)
async def ingest(req: IngestRequest, background_tasks: BackgroundTasks) -> dict:
    raw = base64.b64decode(req.fileContentBase64)
    background_tasks.add_task(run_ingest, req.importId, req.userId, req.source, raw)
    return {"status": "accepted", "importId": str(req.importId)}
