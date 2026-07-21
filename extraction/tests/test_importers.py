"""Parser tests."""
from __future__ import annotations

from pathlib import Path

from app.importers import instapaper, pocket

SAMPLES = Path(__file__).resolve().parents[2] / "samples"


def test_pocket_parses_expected_rows():
    raw = (SAMPLES / "pocket_export_sample.html").read_bytes()
    articles = pocket.parse(raw)

    assert len(articles) == 5
    urls = {a.url for a in articles}
    assert "https://www.gnu.org/philosophy/free-sw.en.html" in urls

    free_sw = next(a for a in articles if "free-sw" in a.url)
    assert free_sw.title == "What is Free Software?"
    assert set(free_sw.tags) == {"foss", "philosophy"}
    assert free_sw.is_archived is False
    assert free_sw.saved_at is not None

    archived = next(a for a in articles if "textsearch-intro" in a.url)
    assert archived.is_archived is True


def test_instapaper_parses_folders_and_status():
    raw = (SAMPLES / "instapaper_export_sample.csv").read_bytes()
    articles = instapaper.parse(raw)

    assert len(articles) == 5

    archived = next(a for a in articles if "rfc3986" in a.url)
    assert archived.is_archived is True

    starred = next(a for a in articles if "gpl-3.0" in a.url)
    assert starred.is_favorite is True

    custom = next(a for a in articles if "wiki/PostgreSQL" in a.url)
    assert custom.tags == ["Reading List"]

    unread = next(a for a in articles if "1342-h" in a.url)
    assert unread.tags == []
    assert unread.excerpt is not None


def test_ignores_non_http_rows():
    csv_text = "URL,Title,Folder\nmailto:x@y.com,Bad,Unread\nhttps://ok.com,Good,Unread\n"
    articles = instapaper.parse(csv_text)
    assert [a.url for a in articles] == ["https://ok.com"]
