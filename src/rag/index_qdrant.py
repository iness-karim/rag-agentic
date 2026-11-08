import json
from pathlib import Path

from fastembed import TextEmbedding
from qdrant_client import QdrantClient, models

MODEL = "intfloat/multilingual-e5-large"
CHUNKS_FILE = Path("data/processed/chunks.jsonl")
DB_PATH = "data/qdrant_db"
COLLECTION = "releases"
BATCH = 32


def main() -> None:
    chunks = [
        json.loads(line)
        for line in CHUNKS_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    embedder = TextEmbedding(model_name=MODEL, cache_dir=".cache/fastembed")

    client = QdrantClient(path=DB_PATH)
    if client.collection_exists(COLLECTION):
        client.delete_collection(COLLECTION)
    client.create_collection(
        COLLECTION,
        vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE),
    )

    for start in range(0, len(chunks), BATCH):
        batch = chunks[start:start + BATCH]
        vectors = list(embedder.embed([f"passage: {c['text']}" for c in batch]))
        client.upsert(
            COLLECTION,
            points=[
                models.PointStruct(id=start + i, vector=v.tolist(), payload=c)
                for i, (c, v) in enumerate(zip(batch, vectors))
            ],
        )
        print(f"{min(start + BATCH, len(chunks))}/{len(chunks)} chunks indexés")

    print("Total dans la base :", client.count(COLLECTION).count)
    client.close()


if __name__ == "__main__":
    main()