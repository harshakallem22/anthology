"""Thin httpx clients for the internal extraction + search services (spec §3.4)."""
from __future__ import annotations

import httpx

from ..config import get_settings

settings = get_settings()


async def trigger_batch_extraction(import_id: str) -> None:
    """Ask the worker to process all pending URLs for an import (fire-and-forget)."""
    url = f"{settings.extraction_service_url}/extract/batch"
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
        await client.post(url, json={"importId": import_id})


async def trigger_single_extraction(article_id: str, url: str) -> None:
    endpoint = f"{settings.extraction_service_url}/extract"
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0)) as client:
        await client.post(endpoint, json={"articleId": article_id, "url": url})


async def proxy_search(params: dict) -> dict:
    """Proxy a search query to the dedicated search service."""
    endpoint = f"{settings.search_service_url}/search"
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(endpoint, params=params)
        resp.raise_for_status()
        return resp.json()
