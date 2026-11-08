import dagster as dg

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


veille_job = dg.define_asset_job("veille_quotidienne", selection=dg.AssetSelection.all())

veille_schedule = dg.ScheduleDefinition(job=veille_job, cron_schedule="0 7 * * *")

defs = dg.Definitions(
    assets=[raw_releases, chunks, qdrant_index],
    jobs=[veille_job],
    schedules=[veille_schedule],
)