import json
from pathlib import Path

for f in sorted(Path("data/raw").glob("*.json")):
    releases = json.loads(f.read_text(encoding="utf-8"))
    if not releases:
        print(f"{f.name}: vide")
        continue
    dates = [r["published_at"][:10] for r in releases if r["published_at"]]
    avg_len = sum(len(r["body"]) for r in releases) // len(releases)
    print(f"{f.name}: {len(releases)} releases, du {min(dates)} au {max(dates)}, ~{avg_len} caractères en moyenne")