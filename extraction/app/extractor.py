"""Article extraction: fetch, extract readable text, sanitize."""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin

import httpx
import nh3
import trafilatura
from bs4 import BeautifulSoup
from trafilatura.metadata import extract_metadata

from .config import get_settings

settings = get_settings()

WORDS_PER_MINUTE = 200

# Substrings that usually mark a non-article image (logos, icons, tracking pixels).
_IMAGE_SKIP = ("logo", "icon", "sprite", "avatar", "favicon", "pixel", "spacer", "1x1")

ALLOWED_TAGS = {
    "p", "br", "hr", "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li", "blockquote", "pre", "code",
    "em", "strong", "b", "i", "a", "img", "figure", "figcaption",
    "table", "thead", "tbody", "tr", "th", "td", "span", "sub", "sup",
}
ALLOWED_ATTRS = {
    "a": {"href", "title"},
    "img": {"src", "alt", "title"},
}


@dataclass
class Extracted:
    title: str | None = None
    byline: str | None = None
    lead_image_url: str | None = None
    excerpt: str | None = None
    content_html: str | None = None
    content_text: str | None = None
    word_count: int | None = None
    reading_minutes: int | None = None
    ok: bool = False


def _sanitize(html: str) -> str:
    return nh3.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS)


def _reading_minutes(word_count: int) -> int:
    return max(1, round(word_count / WORDS_PER_MINUTE))


def _excerpt(text: str, limit: int = 280) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + "…"


def _first_content_image(
    content_html: str | None, raw_html: str, base_url: str | None
) -> str | None:
    """Pick the first usable image from the article body, then the raw page."""
    for source, skip_junk in ((content_html, False), (raw_html, True)):
        if not source:
            continue
        for img in BeautifulSoup(source, "html.parser").find_all("img"):
            src = (img.get("src") or img.get("data-src") or "").strip()
            if not src or src.startswith("data:"):
                continue
            if base_url:
                src = urljoin(base_url, src)
            if not src.lower().startswith(("http://", "https://")):
                continue
            if skip_junk and any(w in src.lower() for w in _IMAGE_SKIP):
                continue
            return src
    return None


def extract_from_html(html: str, url: str | None = None) -> Extracted:
    """Parse readable content + metadata from raw HTML (no network)."""
    if not html or not html.strip():
        return Extracted(ok=False)

    content_html = trafilatura.extract(
        html,
        url=url,
        output_format="html",
        include_images=True,
        include_formatting=True,
        include_links=True,
        favor_recall=True,
    )
    content_text = trafilatura.extract(html, url=url, favor_recall=True)

    if not content_text:
        soup = BeautifulSoup(html, "html.parser")
        content_text = soup.get_text(separator=" ", strip=True) or None
    if not content_text:
        return Extracted(ok=False)

    title = byline = lead_image = None
    try:
        meta = extract_metadata(html, default_url=url)
        if meta is not None:
            title = getattr(meta, "title", None)
            byline = getattr(meta, "author", None)
            lead_image = getattr(meta, "image", None)
    except Exception:
        pass

    if not title:
        soup = BeautifulSoup(html, "html.parser")
        if soup.title and soup.title.string:
            title = soup.title.string.strip()

    if lead_image and url:
        lead_image = urljoin(url, lead_image)
    if not lead_image:
        lead_image = _first_content_image(content_html, html, url)

    word_count = len(content_text.split())
    sanitized_html = _sanitize(content_html) if content_html else None

    return Extracted(
        title=title,
        byline=byline,
        lead_image_url=lead_image,
        excerpt=_excerpt(content_text),
        content_html=sanitized_html,
        content_text=content_text,
        word_count=word_count,
        reading_minutes=_reading_minutes(word_count),
        ok=True,
    )


async def fetch_and_extract(url: str) -> Extracted:
    """Fetch a URL and extract readable content. Network failures → ok=False."""
    try:
        async with httpx.AsyncClient(
            timeout=settings.fetch_timeout_seconds,
            follow_redirects=True,
            headers={"User-Agent": settings.user_agent},
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text
    except (httpx.HTTPError, UnicodeDecodeError):
        return Extracted(ok=False)

    return extract_from_html(html, url=url)
