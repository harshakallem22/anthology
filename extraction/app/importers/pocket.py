"""Pocket export parser."""
from __future__ import annotations

from datetime import datetime, timezone

from bs4 import BeautifulSoup

from .base import ParsedArticle


def _parse_time_added(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromtimestamp(int(raw), tz=timezone.utc)
    except (ValueError, OverflowError, OSError):
        return None


def _parse_tags(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [t.strip() for t in raw.split(",") if t.strip()]


def parse(content: bytes | str) -> list[ParsedArticle]:
    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="replace")
    soup = BeautifulSoup(content, "html.parser")

    articles: list[ParsedArticle] = []
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if not href.lower().startswith(("http://", "https://")):
            continue

        archived = False
        header = anchor.find_previous(["h1", "h2"])
        if header and "archive" in header.get_text(strip=True).lower():
            archived = True

        articles.append(
            ParsedArticle(
                url=href,
                title=anchor.get_text(strip=True) or None,
                saved_at=_parse_time_added(anchor.get("time_added")),
                tags=_parse_tags(anchor.get("tags")),
                is_archived=archived,
            )
        )
    return articles
