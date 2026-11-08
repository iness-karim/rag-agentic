import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

REPOS = [
    "apache/airflow",
    "dagster-io/dagster",
    "apache/iceberg",
    "delta-io/delta",
    "qdrant/qdrant",
    "run-llama/llama_index",
]

RAW_DIR = Path("data/raw")
PER_PAGE = 10


def fetch_releases(repo: str) -> list[dict]:
    headers = {"Accept": "application/vnd.github+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"https://api.github.com/repos/{repo}/releases"
    response = requests.get(url, headers=headers, params={"per_page": PER_PAGE}, timeout=30)
    response.raise_for_status()

    return [
        {
            "repo": repo,
            "name": r["name"] or r["tag_name"],
            "tag": r["tag_name"],
            "published_at": r["published_at"],
            "url": r["html_url"],
            "body": r["body"] or "",
        }
        for r in response.json()
        if not r["draft"]
    ]


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for repo in REPOS:
        releases = fetch_releases(repo)
        out_file = RAW_DIR / f"{repo.replace('/', '__')}.json"
        out_file.write_text(json.dumps(releases, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{repo}: {len(releases)} releases -> {out_file}")


if __name__ == "__main__":
    main()