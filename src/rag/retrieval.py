import re

from qdrant_client import models

K = 5
K_FILTERED = 8

REPO_ALIASES = {
    "apache/airflow": ["airflow"],
    "apache/iceberg": ["iceberg"],
    "dagster-io/dagster": ["dagster"],
    "delta-io/delta": ["delta lake", "delta"],
    "qdrant/qdrant": ["qdrant"],
    "run-llama/llama_index": ["llamaindex", "llama_index", "llama-index", "llama index"],
}

# "v1.19.0", "1.13.29", "v1.20" ; ignore la ponctuation finale
VERSION_RE = re.compile(r"(?<![\w.])v?(\d+\.\d+(?:\.\d+)?)(?!\w|\.\d)")


def build_filter(question: str) -> models.Filter | None:
    low = question.lower()
    conditions = []

    versions = VERSION_RE.findall(question)
    if versions:
        tags = []
        for v in versions:
            tags += [v, f"v{v}"]  # Qdrant tague "v1.19.0", Dagster "1.13.29"
        conditions.append(models.FieldCondition(key="tag", match=models.MatchAny(any=tags)))

    repos = [r for r, names in REPO_ALIASES.items() if any(n in low for n in names)]
    if repos:
        conditions.append(models.FieldCondition(key="repo", match=models.MatchAny(any=repos)))

    return models.Filter(must=conditions) if conditions else None


def retrieve(question: str, embedder, client, k: int | None = None, use_filter: bool = True) -> list[dict]:
    vector = list(embedder.embed([f"query: {question}"]))[0].tolist()
    flt = build_filter(question) if use_filter else None
    if k is None:
        k = K_FILTERED if flt is not None else K
    points = client.query_points("releases", query=vector, query_filter=flt, limit=k).points
    if not points and flt is not None:  # filtre trop strict : recherche complète
        points = client.query_points("releases", query=vector, limit=K).points
    return [p.payload for p in points]