from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo import IndexModel
from pymongo.collection import Collection
from pymongo.database import Database

from app.core.config import get_settings

settings = get_settings()
_mongo_client: MongoClient | None = None
_mongo_db: Database | None = None


def get_mongo_client() -> MongoClient:
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(settings.mongo_uri)
    return _mongo_client


def get_assistant_db() -> Database:
    global _mongo_db
    if _mongo_db is None:
        client = get_mongo_client()
        _mongo_db = client[settings.mongo_db_name]
    return _mongo_db


def close_mongo_connection() -> None:
    global _mongo_client, _mongo_db
    if _mongo_client is not None:
        _mongo_client.close()
    _mongo_client = None
    _mongo_db = None


def ensure_assistant_indexes() -> None:
    db = get_assistant_db()
    db["assistant_sessions"].create_indexes([
        IndexModel([("tenant_id", ASCENDING), ("user_id", ASCENDING), ("updated_at", DESCENDING)],
                   name="tenant_user_updated"),
        IndexModel([("tenant_id", ASCENDING), ("created_at", DESCENDING)],
                   name="tenant_created"),
    ])
    db["assistant_messages"].create_indexes([
        IndexModel([("session_id", ASCENDING), ("created_at", ASCENDING)],
                   name="session_created"),
        IndexModel([("tenant_id", ASCENDING), ("role", ASCENDING)],
                   name="tenant_role"),
    ])
    db["assistant_feedback"].create_indexes([
        IndexModel([("message_id", ASCENDING), ("user_id", ASCENDING)],
                   unique=True, name="message_user_unique"),
        IndexModel([("tenant_id", ASCENDING)],
                   name="tenant"),
    ])
    db["counters"].create_index("_id")
