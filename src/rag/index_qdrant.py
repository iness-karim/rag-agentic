import json
import sys
import uuid
from pathlib import Path

from fastembed import TextEmbedding
from qdrant_client import QdrantClient, models

MODEL = "intfloat/multilingual-e5-large"
CHUNKS_FILE = Path("data/processed/chunks.jsonl")
DB_PATH = "data/qdrant_db"
COLLECTION = "releases"
BATCH = 32


def point_id(chunk_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))


def existing_ids(client: QdrantClient) -> set[str]:
    ids, offset = set(), None
    while True:
        points, offset = client.scroll(
            COLLECTION, limit=500, offset=offset, with_payload=False, with_vectors=False
        )
        ids.update(str(p.id) for p in points)
        if offset is None:
            return ids


def main() -> None:
    rebuild = "--rebuild" in sys.argv
    chunks = [
        json.loads(line)
        for line in CHUNKS_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    client = QdrantClient(path=DB_PATH)
    if rebuild and client.collection_exists(COLLECTION):
        client.delete_collection(COLLECTION)
    if not client.collection_exists(COLLECTION):
        client.create_collection(
            COLLECTION,
            vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE),
        )

    known = existing_ids(client)
    todo = [c for c in chunks if point_id(c["id"]) not in known]
    print(f"{len(chunks)} chunks au total, {len(todo)} nouveau(x) à indexer")

    if todo:
        embedder = TextEmbedding(model_name=MODEL, cache_dir=".cache/fastembed")
        for start in range(0, len(todo), BATCH):
            batch = todo[start:start + BATCH]
            vectors = list(embedder.embed([f"passage: {c['text']}" for c in batch]))
            client.upsert(
                COLLECTION,
                points=[
                    models.PointStruct(id=point_id(c["id"]), vector=v.tolist(), payload=c)
                    for c, v in zip(batch, vectors)
                ],
            )
            print(f"{min(start + BATCH, len(todo))}/{len(todo)} chunks indexés")

    print("Total dans la base :", client.count(COLLECTION).count)
    client.close()


if __name__ == "__main__":
    main()