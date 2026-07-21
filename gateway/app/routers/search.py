"""Search proxy - forwards to the dedicated search service (spec §3.3)."""
from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query

from ..auth.security import current_user
from ..clients.services import proxy_search
from ..models import User
from ..schemas import SearchResults

router = APIRouter(tags=["search"])


@router.get("/search", response_model=SearchResults)
async def search(
    q: str = Query(..., min_length=1),
    tags: str | None = Query(None, description="Comma-separated tag names"),
    limit: int = Query(20, le=100),
    user: User = Depends(current_user),
) -> dict:
    params: dict[str, str | int] = {"q": q, "userId": str(user.id), "limit": limit}
    if tags:
        params["tags"] = tags
    try:
        return await proxy_search(params)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Search unavailable: {exc}") from exc
