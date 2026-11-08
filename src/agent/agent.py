import json
import sys
from pathlib import Path

import requests
from fastembed import TextEmbedding
from qdrant_client import QdrantClient

from src.rag.answer import EMBED_MODEL, LLM_MODEL, OLLAMA_URL, generate
from src.rag.retrieval import REPO_ALIASES, VERSION_RE, retrieve, retrieve_release

RAW_DIR = Path("data/raw")

ROUTER_PROMPT = (
    "Tu choisis l'outil adapté à la question d'un utilisateur. "
    "Appelle latest_release UNIQUEMENT si la question demande quelle est la version ou la release "
    "la plus récente (dernière version publiée) d'un dépôt précis. "
    "Pour toute autre question, appelle search_releases."
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "latest_release",
            "description": "Renvoie la release la plus récente d'un dépôt, triée par date de publication.",
            "parameters": {
                "type": "object",
                "properties": {"repo": {"type": "string", "enum": list(REPO_ALIASES)}},
                "required": ["repo"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_releases",
            "description": "Recherche dans le contenu des releases (fonctionnalités, corrections, dépréciations...).",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


def latest_release(repo: str) -> list[dict]:
    path = RAW_DIR / f"{repo.replace('/', '__')}.json"
    if not path.exists():
        return []
    releases = [r for r in json.loads(path.read_text(encoding="utf-8")) if r["published_at"]]
    if not releases:
        return []
    r = max(releases, key=lambda r: r["published_at"])
    date = r["published_at"][:10]
    text = (
        f"{r['repo']} {r['tag']} ({date}) - Release la plus récente\n"
        f"D'après les dates de publication du corpus, la release la plus récente de {r['repo']} "
        f"est {r['tag']}, publiée le {date}."
    )
    return [{"repo": r["repo"], "tag": r["tag"], "section": "Release la plus récente",
             "url": r["url"], "text": text}]


def choose_tool(question: str) -> tuple[str, dict]:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": ROUTER_PROMPT},
                {"role": "user", "content": question},
            ],
            "tools": TOOLS,
            "stream": False,
            "options": {"temperature": 0},
        },
        timeout=600,
    )
    response.raise_for_status()
    calls = response.json()["message"].get("tool_calls") or []
    if not calls:
        return "search_releases", {}
    fn = calls[0]["function"]
    args = fn.get("arguments") or {}
    if isinstance(args, str):
        args = json.loads(args)
    return fn["name"], args


def agent_answer(question: str, embedder, client) -> tuple[str, list[dict], str]:
    name, args = choose_tool(question)
    if name == "latest_release" and VERSION_RE.search(question):
        name = "search_releases"  # une question qui nomme une version ne demande pas « la dernière »
    chunks = []
    if name == "latest_release":
        chunks = latest_release(args.get("repo", ""))
        if chunks:  # on ajoute le contenu de cette release, pas seulement son tag
            head = chunks[0]
            chunks += retrieve_release(question, head["repo"], head["tag"], embedder, client)
    if not chunks:  # outil inconnu, dépôt invalide ou pas de tool call : recherche classique
        name = "search_releases"
        chunks = retrieve(question, embedder, client)
    return generate(question, chunks), chunks, name


def main() -> None:
    question = " ".join(sys.argv[1:])
    embedder = TextEmbedding(model_name=EMBED_MODEL, cache_dir=".cache/fastembed")
    client = QdrantClient(path="data/qdrant_db")
    answer, chunks, tool = agent_answer(question, embedder, client)
    client.close()
    print(f"[outil : {tool}]\n{answer}\n\nSources :")
    for i, c in enumerate(chunks, start=1):
        print(f"[{i}] {c['repo']} {c['tag']} - {c['section']} | {c['url']}")


if __name__ == "__main__":
    main()