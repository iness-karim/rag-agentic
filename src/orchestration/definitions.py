import dagster as dg

from src.digest import digest
from src.ingestion import clean_chunk, fetch_releases
from src.rag import index_qdrant


@dg.asset(group_name="veille")
def raw_releases() -> None:
    """Releases GitHub fusionnées dans data/raw (seules les nouvelles sont ajoutées)."""
    fetch_releases.main()


@dg.asset(deps=[raw_releases], group_name="veille")
def chunks() -> None:
    """Texte nettoyé et découpé en chunks dans data/processed."""
    clean_chunk.main()


@dg.asset(deps=[chunks], group_name="veille")
def qdrant_index() -> None:
    """Embeddings des nouveaux chunks, ajoutés dans la base Qdrant."""
    index_qdrant.main()


@dg.asset(deps=[raw_releases], group_name="digest")
def weekly_digest() -> None:
    """Résumé en français des releases des 7 derniers jours, écrit dans digests/ (Ollama requis)."""
    digest.main(days=7)


pipeline_job = dg.define_asset_job(
    "veille_quotidienne",
    selection=dg.AssetSelection.assets(raw_releases, chunks, qdrant_index),
)
digest_job = dg.define_asset_job(
    "digest_hebdomadaire",
    selection=dg.AssetSelection.assets(weekly_digest),
)

defs = dg.Definitions(
    assets=[raw_releases, chunks, qdrant_index, weekly_digest],
    jobs=[pipeline_job, digest_job],
    schedules=[
        dg.ScheduleDefinition(job=pipeline_job, cron_schedule="0 7 * * *"),  # chaque jour à 7 h
        dg.ScheduleDefinition(job=digest_job, cron_schedule="0 8 * * 1"),  # chaque lundi à 8 h
    ],
)