import json
import sys
from pathlib import Path

from fastembed import TextEmbedding
from qdrant_client import QdrantClient

from src.rag.retrieval import retrieve

EMBED_MODEL = "intfloat/multilingual-e5-large"
use_filter = "--no-filter" not in sys.argv
k_arg = next((int(a.split("=")[1]) for a in sys.argv if a.startswith("--k=")), None)
print("K :", k_arg or "adaptatif (5 sans filtre, 8 avec filtre)")
print("Filtre repo/tag :", "activé" if use_filter else "désactivé")

lines = Path("eval/questions.jsonl").read_text(encoding="utf-8").splitlines()
questions = [json.loads(l) for l in lines if l.strip()]
questions = [q for q in questions if q["source_url"]]  # sans les questions sans réponse
keywords = json.loads(Path("eval/keywords.json").read_text(encoding="utf-8"))

embedder = TextEmbedding(model_name=EMBED_MODEL, cache_dir=".cache/fastembed")
client = QdrantClient(path="data/qdrant_db")

found = {1: 0, 3: 0, 5: 0}
covered = 0
for q in questions:
    chunks = retrieve(q["question"], embedder, client, k=k_arg, use_filter=use_filter)
    urls = [c["url"] for c in chunks]
    rank = urls.index(q["source_url"]) + 1 if q["source_url"] in urls else None
    for k in found:
        if rank and rank <= k:
            found[k] += 1

    context = " ".join(c["text"] for c in chunks).lower()
    has_answer = all(any(a.lower() in context for a in g) for g in keywords[q["id"]])
    covered += has_answer
    print(f"{q['id']} | rang {rank or '-'} | réponse dans les chunks : {'OK' if has_answer else 'KO'}")

n = len(questions)
print(f"\n{n} questions")
for k, c in found.items():
    print(f"Release retrouvée @{k} : {c}/{n} = {c / n:.0%}")
print(f"Mots-clés de la réponse dans le top 5 : {covered}/{n} = {covered / n:.0%}")
client.close()