import sys

from fastembed import TextEmbedding
from qdrant_client import QdrantClient

MODEL = "intfloat/multilingual-e5-large"

question = " ".join(sys.argv[1:])
embedder = TextEmbedding(model_name=MODEL, cache_dir=".cache/fastembed")
client = QdrantClient(path="data/qdrant_db")

vector = list(embedder.embed([f"query: {question}"]))[0].tolist()
hits = client.query_points("releases", query=vector, limit=5).points

for h in hits:
    p = h.payload
    print(f"{h.score:.3f} | {p['repo']} {p['tag']} | {p['section']}")
    print("   ", p["text"][:160].replace("\n", " "))
client.close()