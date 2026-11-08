import json
from pathlib import Path

from fastembed import TextEmbedding
from qdrant_client import QdrantClient

MODEL = "intfloat/multilingual-e5-large"
K = 5

lines = Path("eval/questions.jsonl").read_text(encoding="utf-8").splitlines()
questions = [json.loads(l) for l in lines if l.strip()]
questions = [q for q in questions if q["source_url"]]  # on exclut les questions sans réponse

embedder = TextEmbedding(model_name=MODEL, cache_dir=".cache/fastembed")
client = QdrantClient(path="data/qdrant_db")
vectors = list(embedder.embed([f"query: {q['question']}" for q in questions]))

found = {1: 0, 3: 0, 5: 0}
for q, v in zip(questions, vectors):
    points = client.query_points("releases", query=v.tolist(), limit=K).points
    urls = [p.payload["url"] for p in points]
    rank = urls.index(q["source_url"]) + 1 if q["source_url"] in urls else None
    for k in found:
        if rank and rank <= k:
            found[k] += 1
    print(f"{q['id']} | rang {rank or '-'} | {q['question'][:70]}")

n = len(questions)
print(f"\n{n} questions")
for k, c in found.items():
    print(f"Recall@{k} : {c}/{n} = {c / n:.0%}")
client.close()