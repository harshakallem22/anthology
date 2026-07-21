"""Pydantic v2 schemas for the gateway API."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserOut(ORMModel):
    id: uuid.UUID
    email: str
    display_name: str | None = None
    avatar_url: str | None = None


class TagOut(ORMModel):
    id: uuid.UUID
    name: str


class TagCreate(BaseModel):
    name: str


class ArticleOut(ORMModel):
    id: uuid.UUID
    url: str
    title: str | None = None
    byline: str | None = None
    lead_image_url: str | None = None
    excerpt: str | None = None
    word_count: int | None = None
    reading_minutes: int | None = None
    saved_at: datetime | None = None
    is_archived: bool
    is_favorite: bool
    extraction_status: str
    created_at: datetime
    tags: list[TagOut] = []


class ArticleDetail(ArticleOut):
    content_html: str | None = None
    content_text: str | None = None


class ArticleUpdate(BaseModel):
    is_archived: bool | None = None
    is_favorite: bool | None = None


class HighlightCreate(BaseModel):
    quote: str
    note: str | None = None
    position: dict | None = None


class HighlightOut(ORMModel):
    id: uuid.UUID
    article_id: uuid.UUID
    quote: str
    note: str | None = None
    position: dict | None = None
    created_at: datetime


class ImportOut(ORMModel):
    id: uuid.UUID
    source: str
    filename: str | None = None
    total_count: int
    processed_count: int
    status: str
    created_at: datetime


class SearchHit(BaseModel):
    id: uuid.UUID
    url: str
    title: str | None = None
    excerpt: str | None = None
    lead_image_url: str | None = None
    reading_minutes: int | None = None
    snippet: str | None = None
    rank: float
    tags: list[str] = []


class SearchResults(BaseModel):
    query: str
    total: int
    results: list[SearchHit]
