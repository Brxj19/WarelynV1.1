"""
One-time migration: copy assistant_sessions, assistant_messages,
assistant_feedback from MySQL to MongoDB.

Usage: .venv/bin/python scripts/migrate_assistant_to_mongo.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pymongo import ReturnDocument
from sqlalchemy import create_engine, text

from app.core.config import get_settings

settings = get_settings()
MONGO_URI = settings.mongo_uri
MONGO_DB = settings.mongo_db_name
MYSQL_URL = settings.database_url


def main():
    print(f"Connecting to MySQL: {MYSQL_URL.split('@')[-1]}")
    engine = create_engine(MYSQL_URL)

    from pymongo import MongoClient
    mongo = MongoClient(MONGO_URI)
    db = mongo[MONGO_DB]

    # ── Sessions ──
    print("\n--- Migrating assistant_sessions ---")
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT id, tenant_id, user_id, title, metadata_json, created_at, updated_at "
            "FROM assistant_sessions ORDER BY id"
        )).mappings().all()
    print(f"  Found {len(rows)} sessions in MySQL")

    mongo_sessions = db["assistant_sessions"]
    mongo_sessions.delete_many({})
    if rows:
        docs = []
        max_id = 0
        for row in rows:
            docs.append({
                "_id": row["id"],
                "id": row["id"],
                "tenant_id": row["tenant_id"],
                "user_id": row["user_id"],
                "title": row["title"],
                "metadata_json": row["metadata_json"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            })
            max_id = max(max_id, row["id"])
        mongo_sessions.insert_many(docs, ordered=False)
        print(f"  Inserted {len(docs)} sessions into MongoDB")
        # Update counter
        db["counters"].find_one_and_update(
            {"_id": "assistant_seq"},
            {"$set": {"seq": max_id}},
            upsert=True,
        )
        print(f"  Counter set to {max_id}")

    # ── Messages ──
    print("\n--- Migrating assistant_messages ---")
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT id, tenant_id, session_id, user_id, role, content, "
            "confidence_score, citations_json, suggested_actions_json, "
            "usage_json, metadata_json, created_at "
            "FROM assistant_messages ORDER BY id"
        )).mappings().all()
    print(f"  Found {len(rows)} messages in MySQL")

    mongo_messages = db["assistant_messages"]
    mongo_messages.delete_many({})
    if rows:
        docs = []
        for row in rows:
            docs.append({
                "_id": row["id"],
                "id": row["id"],
                "tenant_id": row["tenant_id"],
                "session_id": row["session_id"],
                "user_id": row["user_id"],
                "role": row["role"],
                "content": row["content"],
                "confidence_score": row["confidence_score"],
                "citations_json": row["citations_json"],
                "suggested_actions_json": row["suggested_actions_json"],
                "usage_json": row["usage_json"],
                "metadata_json": row["metadata_json"],
                "created_at": row["created_at"],
            })
        mongo_messages.insert_many(docs, ordered=False)
        print(f"  Inserted {len(docs)} messages into MongoDB")

    # ── Feedback ──
    print("\n--- Migrating assistant_feedback ---")
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT id, tenant_id, message_id, user_id, value, note, created_at "
            "FROM assistant_feedback ORDER BY id"
        )).mappings().all()
    print(f"  Found {len(rows)} feedback records in MySQL")

    mongo_feedback = db["assistant_feedback"]
    mongo_feedback.delete_many({})
    if rows:
        docs = []
        for row in rows:
            docs.append({
                "_id": row["id"],
                "id": row["id"],
                "tenant_id": row["tenant_id"],
                "message_id": row["message_id"],
                "user_id": row["user_id"],
                "value": row["value"],
                "note": row["note"],
                "created_at": row["created_at"],
            })
        mongo_feedback.insert_many(docs, ordered=False)
        print(f"  Inserted {len(docs)} feedback records into MongoDB")

    # ── Create indexes ──
    print("\n--- Creating indexes ---")
    from app.db.mongo import ensure_assistant_indexes
    ensure_assistant_indexes()
    print("  Indexes created.")

    # ── Verify ──
    print("\n--- Verification ---")
    print(f"  Sessions:   MongoDB={db['assistant_sessions'].count_documents({})}")
    print(f"  Messages:   MongoDB={db['assistant_messages'].count_documents({})}")
    print(f"  Feedback:   MongoDB={db['assistant_feedback'].count_documents({})}")

    mongo.close()
    print("\nMigration complete.")


if __name__ == "__main__":
    main()
