from src.ingestion.clean_chunk import clean, split_long, split_sections
from src.ingestion.fetch_releases import merge
from src.rag.index_qdrant import point_id
from src.rag.retrieval import build_filter


def test_clean_keeps_label_of_markdown_links():
    assert clean("See [the docs](https://example.com/docs) now") == "See the docs now"


def test_clean_shortens_github_pull_links():
    assert clean("* https://github.com/qdrant/qdrant/pull/9669 - Fix") == "* #9669 - Fix"


def test_clean_normalizes_windows_newlines():
    assert clean("a\r\nb") == "a\nb"


def test_clean_removes_emoji_codes():
    assert clean("Features :point_up:") == "Features"


def test_clean_removes_dash_left_after_link_removal():
    assert clean("* - TurboQuant 4-bit") == "* TurboQuant 4-bit"


def test_split_sections_uses_headings():
    text = "## Features\n- a\n\n## Bug Fixes\n- b"
    assert split_sections(text) == [("Features", "- a"), ("Bug Fixes", "- b")]


def test_split_long_respects_max_chars():
    text = "\n".join(["x" * 100] * 10)
    parts = split_long(text, max_chars=250)
    assert len(parts) > 1
    assert all(len(p) <= 250 for p in parts)


def test_split_long_loses_nothing():
    text = "\n".join(["x" * 100] * 10)
    parts = split_long(text, max_chars=250)
    assert "".join(parts).replace("\n", "") == "x" * 1000


def test_merge_adds_only_new_tags():
    existing = [{"tag": "v1", "published_at": "2026-01-01"}]
    fetched = [
        {"tag": "v1", "published_at": "2026-01-01"},
        {"tag": "v2", "published_at": "2026-02-01"},
    ]
    merged, n_new = merge(existing, fetched)
    assert n_new == 1
    assert [r["tag"] for r in merged] == ["v2", "v1"]


def test_merge_with_nothing_new():
    existing = [{"tag": "v1", "published_at": "2026-01-01"}]
    merged, n_new = merge(existing, list(existing))
    assert n_new == 0
    assert len(merged) == 1


def test_point_id_is_stable_and_unique():
    assert point_id("qdrant__qdrant__v1.19.0__0") == point_id("qdrant__qdrant__v1.19.0__0")
    assert point_id("qdrant__qdrant__v1.19.0__0") != point_id("qdrant__qdrant__v1.19.0__1")


def test_build_filter_detects_version_and_repo():
    f = build_filter("Quelle faille dans Qdrant v1.19.0 ?")
    assert {c.key for c in f.must} == {"tag", "repo"}


def test_build_filter_without_hints_is_none():
    assert build_filter("Quoi de neuf cette semaine ?") is None


def test_build_filter_ignores_dates():
    f = build_filter("Quelle est la version de Dagster la plus récente au 8 novembre 2026 ?")
    assert {c.key for c in f.must} == {"repo"}