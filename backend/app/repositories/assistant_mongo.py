from datetime import datetime, timezone

from pymongo import ReturnDocument

from app.db.mongo import get_assistant_db


class AssistantMongoRepository:
    def __init__(self) -> None:
        self.db = get_assistant_db()
        self.sessions = self.db["assistant_sessions"]
        self.messages = self.db["assistant_messages"]
        self.feedback = self.db["assistant_feedback"]

    def _next_id(self) -> int:
        counter = self.db["counters"].find_one_and_update(
            {"_id": "assistant_seq"},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return counter["seq"]

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    # ── Sessions ──

    def create_session(
        self,
        *,
        tenant_id: int,
        user_id: int,
        title: str,
    ) -> dict:
        doc_id = self._next_id()
        now = self._now()
        doc = {
            "_id": doc_id,
            "id": doc_id,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "title": title,
            "metadata_json": None,
            "created_at": now,
            "updated_at": now,
        }
        self.sessions.insert_one(doc)
        return doc

    def get_session(self, *, tenant_id: int, session_id: int) -> dict | None:
        return self.sessions.find_one(
            {"id": session_id, "tenant_id": tenant_id},
            {"_id": False},
        )

    def list_sessions_for_user(self, *, tenant_id: int, user_id: int) -> list[dict]:
        return list(
            self.sessions.find(
                {"tenant_id": tenant_id, "user_id": user_id},
                {"_id": False},
            ).sort("updated_at", -1)
        )

    def update_session_timestamp(self, session_id: int) -> None:
        self.sessions.update_one(
            {"id": session_id},
            {"$set": {"updated_at": self._now()}},
        )

    def update_session_title(self, session_id: int, title: str) -> None:
        self.sessions.update_one(
            {"id": session_id},
            {"$set": {"title": title, "updated_at": self._now()}},
        )

    def delete_session(self, *, tenant_id: int, session_id: int) -> bool:
        session = self.sessions.find_one({"id": session_id, "tenant_id": tenant_id}, {"_id": True})
        if not session:
            return False
        message_ids = [m["id"] for m in self.messages.find({"session_id": session_id}, {"id": 1})]
        self.messages.delete_many({"session_id": session_id})
        if message_ids:
            self.feedback.delete_many({"message_id": {"$in": message_ids}})
        self.sessions.delete_one({"_id": session["_id"]})
        return True

    # ── Messages ──

    def create_message(
        self,
        *,
        tenant_id: int,
        session_id: int,
        user_id: int | None,
        role: str,
        content: str,
        confidence_score: float | None = None,
        citations_json: list[dict] | None = None,
        suggested_actions_json: list[dict] | None = None,
        usage_json: dict | None = None,
        metadata_json: dict | None = None,
    ) -> dict:
        doc_id = self._next_id()
        now = self._now()
        doc = {
            "_id": doc_id,
            "id": doc_id,
            "tenant_id": tenant_id,
            "session_id": session_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "confidence_score": confidence_score,
            "citations_json": citations_json,
            "suggested_actions_json": suggested_actions_json,
            "usage_json": usage_json,
            "metadata_json": metadata_json,
            "created_at": now,
        }
        self.messages.insert_one(doc)
        return doc

    def list_messages(self, *, tenant_id: int, session_id: int) -> list[dict]:
        return list(
            self.messages.find(
                {"session_id": session_id},
                {"_id": False},
            ).sort("created_at", 1)
        )
    
    def count_messages(self, *, tenant_id: int, session_id: int) -> int:
        return self.messages.count_documents({"session_id": session_id, "tenant_id": tenant_id})

    def list_messages_for_telemetry(self, *, tenant_id: int) -> list[dict]:
        return list(
            self.messages.find(
                {"tenant_id": tenant_id, "role": "ASSISTANT"},
                {"_id": False},
            )
        )

    def get_message(self, *, tenant_id: int, message_id: int) -> dict | None:
        return self.messages.find_one(
            {"id": message_id, "tenant_id": tenant_id},
            {"_id": False},
        )

    # ── Feedback ──

    def upsert_feedback(
        self,
        *,
        tenant_id: int,
        message_id: int,
        user_id: int,
        value: str,
        note: str | None,
    ) -> dict:
        existing = self.feedback.find_one({"message_id": message_id, "user_id": user_id})
        if existing:
            self.feedback.update_one(
                {"_id": existing["_id"]},
                {"$set": {"value": value, "note": note}},
            )
            existing["value"] = value
            existing["note"] = note
            return existing
        doc_id = self._next_id()
        now = self._now()
        doc = {
            "_id": doc_id,
            "id": doc_id,
            "tenant_id": tenant_id,
            "message_id": message_id,
            "user_id": user_id,
            "value": value,
            "note": note,
            "created_at": now,
        }
        self.feedback.insert_one(doc)
        return doc

    # ── Telemetry ──

    def get_telemetry(self, *, tenant_id: int) -> dict:
        rows = self.list_messages_for_telemetry(tenant_id=tenant_id)
        total = len(rows)
        if total == 0:
            return {
                "total_requests": 0,
                "avg_latency_ms": 0.0,
                "total_tokens": 0,
                "abstain_rate_pct": 0.0,
                "citation_rate_pct": 0.0,
            }
        latency_values = [
            float((row.get("metadata_json") or {}).get("latency_ms", 0.0))
            for row in rows
        ]
        abstains = [
            row for row in rows
            if (row.get("metadata_json") or {}).get("abstained") is True
        ]
        citation_count = [
            row for row in rows if row.get("citations_json")
        ]
        total_tokens = sum(
            int((row.get("usage_json") or {}).get("total_tokens", 0))
            for row in rows
        )
        return {
            "total_requests": total,
            "avg_latency_ms": round(sum(latency_values) / total, 2),
            "total_tokens": total_tokens,
            "abstain_rate_pct": round((len(abstains) * 100.0) / total, 2),
            "citation_rate_pct": round((len(citation_count) * 100.0) / total, 2),
        }
