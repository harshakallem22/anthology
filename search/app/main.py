"""Search service HTTP surface (internal REST, spec §3.3)."""
from __future__ import annotations

import uuid

from fastapi import Depends, FastAPI, Query
from sqlalchemy.ext.asyncio import AsyncSession

from .db import get_session
from .search import search as run_search

app = FastAPI(title="Anthology Search Service", version="1.0.0")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "search"}


@app.get("/search")
async def search(
    q: str = Query(..., min_length=1),
    userId: uuid.UUID = Query(...),
    tags: str | None = Query(None),
    limit: int = Query(20, le=100),
    session: AsyncSession = Depends(get_session),
) -> dict:
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None
    return await run_search(
        session, user_id=userId, query=q, tags=tag_list, limit=limit
    )
