"""Shared shape for parsed import rows."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ParsedArticle:
    url: str
    title: str | None = None
    saved_at: datetime | None = None
    tags: list[str] = field(default_factory=list)
    is_archived: bool = False
    is_favorite: bool = False
    excerpt: str | None = None
