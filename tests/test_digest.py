import json
from datetime import datetime, timedelta, timezone

from src.digest import digest


def test_recent_releases_keeps_only_recent_ones(tmp_path, monkeypatch):
    now = datetime.now(timezone.utc)
    old = (now - timedelta(days=30)).isoformat()
    new = (now - timedelta(days=1)).isoformat()
    data = [{"tag": "old", "published_at": old}, {"tag": "new", "published_at": new}]
    (tmp_path / "x.json").write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(digest, "RAW_DIR", tmp_path)

    assert [r["tag"] for r in digest.recent_releases(7)] == ["new"]