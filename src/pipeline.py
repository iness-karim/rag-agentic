from src.ingestion import clean_chunk, fetch_releases
from src.rag import index_qdrant


def main() -> None:
    print("--- 1/3 Récupération des releases ---")
    fetch_releases.main()
    print("\n--- 2/3 Nettoyage et découpage ---")
    clean_chunk.main()
    print("\n--- 3/3 Indexation ---")
    index_qdrant.main()


if __name__ == "__main__":
    main()