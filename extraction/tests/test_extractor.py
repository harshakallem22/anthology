"""Extraction tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.extractor import extract_from_html, fetch_and_extract

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample_article.html"


def test_extract_from_local_fixture():
    html = FIXTURE.read_text()
    result = extract_from_html(html, url="https://example.com/owning-your-reading")

    assert result.ok is True
    assert result.title == "The Quiet Value of Owning Your Reading"
    assert result.content_text and "read-later tool" in result.content_text
    assert result.word_count and result.word_count > 40
    assert result.reading_minutes and result.reading_minutes >= 1

    assert "Subscribe" not in (result.content_text or "")
    assert "buy our newsletter" not in (result.content_text or "")


def test_sanitized_html_has_no_scripts():
    html = (
        "<html><head><title>T</title></head><body><article>"
        "<p>Hello world this is a body paragraph with enough words to extract "
        "cleanly from the document under test.</p>"
        "<script>alert('xss')</script></article></body></html>"
    )
    result = extract_from_html(html, url="https://example.com/x")
    assert result.content_html is not None
    assert "<script" not in result.content_html.lower()


def test_lead_image_falls_back_to_first_body_image():
    """When there's no og:image, use the first article image (relative → absolute)."""
    html = (
        "<html><head><title>T</title></head><body><article>"
        "<p>A body paragraph with enough words to extract cleanly from the "
        "document under test here.</p>"
        '<img src="/media/photo.jpg" alt="x"></article></body></html>'
    )
    result = extract_from_html(html, url="https://blog.example.com/post")
    assert result.lead_image_url == "https://blog.example.com/media/photo.jpg"


def test_empty_html_is_not_ok():
    assert extract_from_html("", url="https://example.com").ok is False


@pytest.mark.asyncio
async def test_failed_fetch_returns_not_ok(monkeypatch):
    result = await fetch_and_extract("http://localhost:1/definitely-not-listening")
    assert result.ok is False
