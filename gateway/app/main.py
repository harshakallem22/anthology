"""Gateway / BFF - the fast, user-facing front door (spec §3.1)."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth.router import router as auth_router
from .config import get_settings
from .routers import articles, export, highlights, imports, search, tags

settings = get_settings()

app = FastAPI(
    title="Anthology Gateway",
    version="1.0.0",
    description="Self-hostable read-later API: imports, articles, tags, highlights, search, export.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(imports.router)
app.include_router(articles.router)
app.include_router(tags.router)
app.include_router(highlights.router)
app.include_router(search.router)
app.include_router(export.router)


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {
        "status": "ok",
        "service": "gateway",
        "google_oauth": settings.google_oauth_enabled,
        "env": settings.env,
    }
