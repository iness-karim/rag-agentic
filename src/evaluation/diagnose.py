import json
from pathlib import Path

from fastembed import TextEmbedding
from qdrant_client import QdrantClient

from src.rag.answer import EMBED_MODEL, retrieve


def read_jsonl(path: str) -> list[dict]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [json.loads(l) for l in lines if l.strip()]


questions = [q for q in read_jsonl("eval/questions.jsonl") if q["type"] != "sans_reponse"]
keywords = json.loads(Path("eval/keywords.json").read_text(encoding="utf-8"))
answers = {a["id"]: a for a in read_jsonl("eval/results/generation_answers.jsonl")}

embedder = TextEmbedding(model_name=EMBED_MODEL, cache_dir=".cache/fastembed")
client = QdrantClient(path="data/qdrant_db")

for q in questions:
    a = answers[q["id"]]
    if a["content_ok"]:
        continue
    chunks = retrieve(q["question"], embedder, client)
    context = " ".join(c["text"] for c in chunks).lower()
    in_context = all(any(k.lower() in context for k in g) for g in keywords[q["id"]])
    refused = "je ne sais pas" in a["answer"].lower()

    if not in_context:
        cause = "RETRIEVAL : l'information n'est pas dans les 5 chunks"
    elif refused:
        cause = "REFUS A TORT : l'information était dans les chunks"
    else:
        cause = "GENERATION ou MOTS-CLES : information présente, réponse non conforme"

    print(f"\n{q['id']} | {cause}")
    print("   Réponse :", a["answer"][:300].replace("\n", " "))

client.close()