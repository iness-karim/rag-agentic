import json
import re
from pathlib import Path

from fastembed import TextEmbedding
from qdrant_client import QdrantClient

from src.rag.answer import EMBED_MODEL, generate, retrieve

lines = Path("eval/questions.jsonl").read_text(encoding="utf-8").splitlines()
questions = [json.loads(l) for l in lines if l.strip()]
keywords = json.loads(Path("eval/keywords.json").read_text(encoding="utf-8"))

embedder = TextEmbedding(model_name=EMBED_MODEL, cache_dir=".cache/fastembed")
client = QdrantClient(path="data/qdrant_db")

rows = []
for q in questions:
    chunks = retrieve(q["question"], embedder, client)
    answer = generate(q["question"], chunks)
    low = answer.lower()
    refused = "je ne sais pas" in low

    if q["type"] == "sans_reponse":
        content_ok, cite_ok = refused, None
    else:
        groups = keywords[q["id"]]
        content_ok = (not refused) and all(any(a.lower() in low for a in g) for g in groups)
        cited = {int(n) for n in re.findall(r"\[(\d+)\]", answer)}
        cited_urls = {chunks[n - 1]["url"] for n in cited if 1 <= n <= len(chunks)}
        cite_ok = q["source_url"] in cited_urls

    rows.append({"id": q["id"], "type": q["type"], "content_ok": content_ok,
                 "cite_ok": cite_ok, "answer": answer})
    cite = "-" if cite_ok is None else ("OK" if cite_ok else "KO")
    print(f"{q['id']} | contenu {'OK' if content_ok else 'KO'} | citation {cite} | {q['question'][:50]}")

client.close()

Path("eval/results").mkdir(parents=True, exist_ok=True)
with open("eval/results/generation_answers.jsonl", "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

answerable = [r for r in rows if r["type"] != "sans_reponse"]
refusals = [r for r in rows if r["type"] == "sans_reponse"]
print(f"\nContenu correct   : {sum(r['content_ok'] for r in answerable)}/{len(answerable)}")
print(f"Citation correcte : {sum(bool(r['cite_ok']) for r in answerable)}/{len(answerable)}")
print(f"Refus corrects    : {sum(r['content_ok'] for r in refusals)}/{len(refusals)}")