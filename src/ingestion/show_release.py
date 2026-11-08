import json
import sys
from pathlib import Path

# usage: python -m src.ingestion.show_release qdrant__qdrant 0
name, index = sys.argv[1], int(sys.argv[2])
releases = json.loads(Path(f"data/raw/{name}.json").read_text(encoding="utf-8"))

if len(sys.argv) < 3 or index >= len(releases):
    sys.exit("index invalide")

r = releases[index]
print(f"{r['repo']} | {r['tag']} | {r['published_at'][:10]}\n{r['url']}\n")
print(r["body"][:4000])