import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

from src.ingestion.clean_chunk import clean
from src.rag.answer import LLM_MODEL, OLLAMA_URL

RAW_DIR = Path("data/raw")
OUT_DIR = Path("digests")
MAX_CHARS = 6000  # on ne donne au modèle que le début de la release

PROMPT = (
    "Tu écris un résumé pour une veille technique à partir d'une note de version (release). "
    "Réponds en français correct avec AU MAXIMUM 5 puces, chacune d'une phrase complète et courte. "
    "Choisis les changements les plus importants pour un utilisateur : nouvelles fonctionnalités, "
    "changements de comportement par défaut, failles de sécurité. Regroupe les changements similaires. "
    "Ne commence pas les puces par une étiquette ou une catégorie. "
    "Utilise uniquement le texte fourni et n'invente rien. Garde tels quels les noms d'options, "
    "de fonctions et de produits. Pas d'introduction ni de conclusion."
)


def recent_releases(days: int) -> list[dict]:
    limit = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    found = []
    for f in sorted(RAW_DIR.glob("*.json")):
        for r in json.loads(f.read_text(encoding="utf-8")):
            if r["published_at"] and r["published_at"][:10] >= limit:
                found.append(r)
    return sorted(found, key=lambda r: r["published_at"], reverse=True)


def limit_bullets(text: str, n: int = 5) -> str:
    """Filet de sécurité : garde les n premières puces si le modèle en a écrit trop."""
    kept, count = [], 0
    for line in text.splitlines():
        if line.lstrip().startswith(("-", "*")) and not line.startswith((" ", "\t")):
            count += 1
            if count > n:
                break
        kept.append(line)
    return "\n".join(kept).strip()

def summarize(release: dict) -> str:
    body = clean(release["body"])[:MAX_CHARS]
    if not body.strip():
        return "Aucune note de version publiée."
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": PROMPT},
                {"role": "user", "content": f"{release['repo']} {release['tag']}\n\n{body}\n\nRappel : 5 puces au maximum, une phrase courte chacune."},
            ],
            "stream": False,
            "options": {"temperature": 0},
        },
        timeout=600,
    )
    response.raise_for_status()
    return limit_bullets(response.json()["message"]["content"].strip())


def main(days: int | None = None) -> None:
    if days is None:
        days = next((int(a.split("=")[1]) for a in sys.argv if a.startswith("--days=")), 7)
    releases = recent_releases(days)
    today = date.today().isoformat()

    lines = [
        f"# Veille data engineering et IA - {today}",
        "",
        f"Releases publiées sur les {days} derniers jours : {len(releases)}.",
        "",
    ]
    for r in releases:
        print(f"Résumé de {r['repo']} {r['tag']}...")
        lines += [
            f"## {r['repo']} {r['tag']} ({r['published_at'][:10]})",
            "",
            summarize(r),
            "",
            f"Source : {r['url']}",
            "",
        ]

    OUT_DIR.mkdir(exist_ok=True)
    out = OUT_DIR / f"digest_{today}.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Digest écrit dans {out}")


if __name__ == "__main__":
    main()