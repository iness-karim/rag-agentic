import sys

import requests
from src.rag.retrieval import K, retrieve
from fastembed import TextEmbedding
from qdrant_client import QdrantClient

EMBED_MODEL = "intfloat/multilingual-e5-large"
LLM_MODEL = "qwen2.5:7b"
OLLAMA_URL = "http://localhost:11434/api/chat"


SYSTEM_PROMPT = (
    "Tu es un assistant de veille technique. Réponds en français, uniquement à partir des "
    "extraits fournis. Cite les extraits utilisés entre crochets, par exemple [1]. "
    "Si les extraits ne contiennent pas la réponse, réponds exactement : "
    "\"Je ne sais pas : le corpus ne contient pas cette information.\" "
    "N'invente rien et n'utilise pas tes connaissances personnelles."
)




def generate(question: str, chunks: list[dict]) -> str:
    context = "\n\n".join(f"[{i}] {c['text']}" for i, c in enumerate(chunks, start=1))
    user_prompt = f"Extraits :\n{context}\n\nQuestion : {question}"
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {"temperature": 0},
        },
        timeout=600,
    )
    response.raise_for_status()
    return response.json()["message"]["content"]


def main() -> None:
    question = " ".join(sys.argv[1:])
    embedder = TextEmbedding(model_name=EMBED_MODEL, cache_dir=".cache/fastembed")
    client = QdrantClient(path="data/qdrant_db")
    chunks = retrieve(question, embedder, client)
    client.close()

    print(generate(question, chunks))
    print("\nSources :")
    for i, c in enumerate(chunks, start=1):
        print(f"[{i}] {c['repo']} {c['tag']} - {c['section']} | {c['url']}")


if __name__ == "__main__":
    main()