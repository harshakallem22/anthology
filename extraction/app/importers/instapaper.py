"""Instapaper export parser."""
from __future__ import annotations

import csv
import io
from datetime import datetime, timezone

from .base import ParsedArticle

_KNOWN_FOLDERS = {"unread", "archive", "starred"}


def _parse_timestamp(raw: str | None) -> datetime | None:
    if not raw:
        return None
    raw = raw.strip()
    if raw.isdigit():
        try:
            return datetime.fromtimestamp(int(raw), tz=timezone.utc)
        except (ValueError, OverflowError, OSError):
            return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def parse(content: bytes | str) -> list[ParsedArticle]:
    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="replace")

    reader = csv.DictReader(io.StringIO(content))
    articles: list[ParsedArticle] = []
    for row in reader:
        norm = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
        url = norm.get("url")
        if not url or not url.lower().startswith(("http://", "https://")):
            continue

        folder = norm.get("folder", "")
        folder_l = folder.lower()
        archived = folder_l == "archive"
        favorite = folder_l == "starred"
        tags = [] if folder_l in _KNOWN_FOLDERS or not folder else [folder]

        articles.append(
            ParsedArticle(
                url=url,
                title=norm.get("title") or None,
                saved_at=_parse_timestamp(norm.get("timestamp")),
                tags=tags,
                is_archived=archived,
                is_favorite=favorite,
                excerpt=norm.get("selection") or None,
            )
        )
    return articles
