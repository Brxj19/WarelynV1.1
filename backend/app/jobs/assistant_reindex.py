from sqlalchemy.orm import Session

from app.services.assistant import AssistantService


def run_assistant_reindex(db: Session) -> dict[str, int]:
    """
    Incremental sync hook for scheduled jobs.
    Current behavior reindexes curated global sources.
    """
    return AssistantService(db).reindex_global_knowledge()
