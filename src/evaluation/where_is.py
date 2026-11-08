import sys

from fastembed import TextEmbedding
from qdrant_client import QdrantClient

from src.rag.answer import EMBED_MODEL
from src.rag.retrieval import build_filter

question, needle = sys.argv[1], sys.argv[2]
embedder = TextEmbedding(model_name=EMBED_MODEL, cache_dir=".cache/fastembed")
client = QdrantClient(path="data/qdrant_db")

vector = list(embedder.embed([f"query: {question}"]))[0].tolist()
points = client.query_points(
    "releases", query=vector, query_filter=build_filter(question), limit=200
).points

print(len(points), "chunks candidats après filtre")
for rank, p in enumerate(points, start=1):
    if needle.lower() in p.payload["text"].lower():
        print(f"rang {rank} | score {p.score:.3f} | {p.payload['tag']} | {p.payload['section']} | {len(p.payload['text'])} caractères")
        print("   ", p.payload["text"][:300].replace("\n", " "))
client.close()