import hashlib
import json
import math
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.models.assistant import (
    AssistantFeedbackValue,
    AssistantMessage,
    AssistantMessageRole,
    AssistantSession,
    FAQChunk,
    KnowledgeSourceType,
)
from app.models.auth import UserRole
from app.models.workflow import WorkflowTaskStatus
from app.repositories.assistant import AssistantRepository
from app.repositories.audit import AuditLogRepository
from app.repositories.reports import ReportsRepository
from app.repositories.workflow import WorkflowRepository


class AssistantService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = AssistantRepository(db)
        self.audit_repository = AuditLogRepository(db)
        self.reports_repository = ReportsRepository(db)
        self.workflow_repository = WorkflowRepository(db)
        self.settings = get_settings()

    def ensure_bootstrap_index(self) -> None:
        if self.repository.count_chunks(None) > 0:
            return
        self.reindex_global_knowledge()

    def reindex_global_knowledge(self) -> dict[str, int]:
        sources = self._knowledge_sources()
        chunks_indexed = 0
        documents_indexed = 0
        for source in sources:
            checksum = hashlib.sha256(source["body_text"].encode("utf-8")).hexdigest()
            document = self.repository.upsert_document(
                tenant_id=None,
                slug=source["slug"],
                title=source["title"],
                source_type=source["source_type"],
                source_uri=source.get("source_uri"),
                body_text=source["body_text"],
                metadata_json=source.get("metadata_json"),
                checksum=checksum,
            )
            chunk_rows = self._chunk_text(
                source["body_text"],
                source_uri=source.get("source_uri"),
                title=source["title"],
                source_type=source["source_type"].value,
                action_to=source.get("action_to"),
            )
            embeddings = self._embed_many([row["content"] for row in chunk_rows])
            for index, row in enumerate(chunk_rows):
                row["embedding"] = embeddings[index] if index < len(embeddings) else None
            self.repository.replace_chunks(document_id=document.id, tenant_id=None, chunks=chunk_rows)
            documents_indexed += 1
            chunks_indexed += len(chunk_rows)
        self.db.commit()
        self._audit_event(
            tenant_id=None,
            actor_user_id=None,
            actor_role="SYSTEM",
            action="ASSISTANT_REINDEX",
            entity_type="assistant_knowledge",
            entity_id="global",
            metadata={
                "documents_indexed": documents_indexed,
                "chunks_indexed": chunks_indexed,
            },
        )
        return {"documents_indexed": documents_indexed, "chunks_indexed": chunks_indexed}

    def faq_suggestions(self, role: UserRole) -> list[dict[str, str]]:
        shared = [
            {"question": "How does the SO to fulfillment flow work?", "description": "Understand order confirmation, pick, pack and commit flow."},
            {"question": "How do I fix reconciliation mismatches?", "description": "Learn how to inspect and resolve inventory mismatches safely."},
            {"question": "What does each workflow task status mean?", "description": "OPEN, IN_PROGRESS, COMPLETED, CANCELLED meanings and expected next actions."},
        ]
        role_specific = {
            UserRole.TENANT_ADMIN: [
                {"question": "What needs my attention today?", "description": "Summarized cross-team bottlenecks and pending approvals."},
                {"question": "Why are invoices/bills pending?", "description": "Find upstream blockers and suggested operational actions."},
            ],
            UserRole.INVENTORY_MANAGER: [
                {"question": "Which low-stock items are most urgent?", "description": "Prioritize replenishment and warehouse actions."},
            ],
            UserRole.SALES_STAFF: [
                {"question": "Which orders are at risk of delay?", "description": "Identify sales orders blocked by stock or workflow."},
            ],
            UserRole.PURCHASE_STAFF: [
                {"question": "Which receipts still need bill recording?", "description": "Find purchase records still pending financial completion."},
            ],
            UserRole.VIEWER: [
                {"question": "Show me current operational health summary.", "description": "Read-only overview of sales, purchasing and stock indicators."},
            ],
        }
        return shared + role_specific.get(role, [])

    def ask_faq(self, *, tenant_id: int, user_id: int, role: UserRole, question: str) -> dict[str, Any]:
        started = time.perf_counter()
        candidates = self._retrieve_chunks(tenant_id=tenant_id, question=question)
        context_blocks = [self._context_block(row) for row in candidates]
        answer_payload, usage = self._grounded_answer(
            question=question,
            context_blocks=context_blocks,
            mode="faq",
            tenant_snapshot=None,
        )
        result = self._apply_confidence_policy(answer_payload, candidates)
        result["latency_ms"] = round((time.perf_counter() - started) * 1000, 2)
        result["usage"] = usage
        self._audit_event(
            tenant_id=tenant_id,
            actor_user_id=user_id,
            actor_role=role.value,
            action="ASSISTANT_FAQ_ASK",
            entity_type="assistant_faq",
            entity_id=None,
            metadata={
                "question_length": len(question),
                "confidence": result.get("confidence"),
                "abstained": bool(result.get("abstained")),
                "citation_count": len(result.get("citations") or []),
                "latency_ms": result["latency_ms"],
                "token_usage": usage.get("total_tokens", 0),
            },
        )
        return result

    def create_session(self, *, tenant_id: int, user_id: int, title: str | None = None) -> AssistantSession:
        session = self.repository.create_session(
            tenant_id=tenant_id,
            user_id=user_id,
            title=title or "New Assistant Session",
        )
        self.db.commit()
        self.db.refresh(session)
        self._audit_event(
            tenant_id=tenant_id,
            actor_user_id=user_id,
            actor_role=UserRole.TENANT_ADMIN.value,
            action="ASSISTANT_SESSION_CREATE",
            entity_type="assistant_session",
            entity_id=str(session.id),
            metadata={"title": session.title},
        )
        return session

    def get_session_detail(self, *, tenant_id: int, user_id: int, session_id: int) -> dict[str, Any]:
        session = self.repository.get_session(tenant_id=tenant_id, session_id=session_id)
        if session is None or session.user_id != user_id:
            raise AppError("ASSISTANT_SESSION_NOT_FOUND", "Assistant session not found.", 404)
        messages = self.repository.list_messages(tenant_id=tenant_id, session_id=session_id)
        return {"session": session, "messages": messages}

    def ask_session(
        self,
        *,
        tenant_id: int,
        user_id: int,
        role: UserRole,
        session_id: int,
        question: str,
    ) -> dict[str, Any]:
        session = self.repository.get_session(tenant_id=tenant_id, session_id=session_id)
        if session is None or session.user_id != user_id:
            raise AppError("ASSISTANT_SESSION_NOT_FOUND", "Assistant session not found.", 404)

        started = time.perf_counter()
        self.repository.create_message(
            tenant_id=tenant_id,
            session_id=session_id,
            user_id=user_id,
            role=AssistantMessageRole.USER.value,
            content=question,
        )
        history = self.repository.list_messages(tenant_id=tenant_id, session_id=session_id)[-8:]
        candidates = self._retrieve_chunks(tenant_id=tenant_id, question=question)
        context_blocks = [self._context_block(row) for row in candidates]
        tenant_snapshot = self._tenant_admin_snapshot(tenant_id) if role == UserRole.TENANT_ADMIN else None
        answer_payload, usage = self._grounded_answer(
            question=question,
            context_blocks=context_blocks,
            mode="copilot",
            tenant_snapshot=tenant_snapshot,
            history=history,
        )
        result = self._apply_confidence_policy(answer_payload, candidates)
        assistant_message = self.repository.create_message(
            tenant_id=tenant_id,
            session_id=session_id,
            user_id=None,
            role=AssistantMessageRole.ASSISTANT.value,
            content=result["answer"],
            confidence_score=result["confidence_score"],
            citations_json=result["citations"],
            suggested_actions_json=result["suggested_actions"],
            usage_json=usage,
            metadata_json={
                "mode": "copilot",
                "confidence": result["confidence"],
                "abstained": bool(result.get("abstained")),
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            },
        )
        session.updated_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(assistant_message)
        result["message"] = assistant_message
        self._audit_event(
            tenant_id=tenant_id,
            actor_user_id=user_id,
            actor_role=role.value,
            action="ASSISTANT_COPILOT_ASK",
            entity_type="assistant_session",
            entity_id=str(session_id),
            metadata={
                "question_length": len(question),
                "confidence": result.get("confidence"),
                "abstained": bool(result.get("abstained")),
                "citation_count": len(result.get("citations") or []),
                "token_usage": usage.get("total_tokens", 0),
            },
        )
        return result

    def add_feedback(
        self,
        *,
        tenant_id: int,
        user_id: int,
        message_id: int,
        value: str,
        note: str | None,
    ):
        message = self.repository.get_message(tenant_id=tenant_id, message_id=message_id)
        if message is None:
            raise AppError("ASSISTANT_MESSAGE_NOT_FOUND", "Assistant message was not found.", 404)
        feedback = self.repository.upsert_feedback(
            tenant_id=tenant_id,
            message_id=message_id,
            user_id=user_id,
            value=value,
            note=note,
        )
        self.db.commit()
        self.db.refresh(feedback)
        self._audit_event(
            tenant_id=tenant_id,
            actor_user_id=user_id,
            actor_role=UserRole.TENANT_ADMIN.value,
            action="ASSISTANT_FEEDBACK",
            entity_type="assistant_message",
            entity_id=str(message_id),
            metadata={"value": value, "has_note": bool(note)},
        )
        return feedback

    def telemetry(self, *, tenant_id: int) -> dict[str, Any]:
        rows = list(
            self.db.scalars(
                select(AssistantMessage).where(
                    AssistantMessage.tenant_id == tenant_id,
                    AssistantMessage.role == AssistantMessageRole.ASSISTANT.value,
                )
            )
        )
        total = len(rows)
        if total == 0:
            return {
                "total_requests": 0,
                "avg_latency_ms": 0.0,
                "total_tokens": 0,
                "abstain_rate_pct": 0.0,
                "citation_rate_pct": 0.0,
            }
        latency_values = [float((row.metadata_json or {}).get("latency_ms", 0.0)) for row in rows]
        abstains = [row for row in rows if (row.metadata_json or {}).get("abstained") is True]
        citation_count = [row for row in rows if row.citations_json]
        total_tokens = sum(int((row.usage_json or {}).get("total_tokens", 0)) for row in rows)
        return {
            "total_requests": total,
            "avg_latency_ms": round(sum(latency_values) / total, 2),
            "total_tokens": total_tokens,
            "abstain_rate_pct": round((len(abstains) * 100.0) / total, 2),
            "citation_rate_pct": round((len(citation_count) * 100.0) / total, 2),
        }

    def _knowledge_sources(self) -> list[dict[str, Any]]:
        root = Path(__file__).resolve().parents[3]
        sources: list[dict[str, Any]] = []
        source_files = [
            ("docs/WARELYN_REAL_WORLD_V2_PRD.md", "Product Requirements", "/reports"),
            ("docs/MODULE_BOUNDARIES.md", "Module Boundaries", "/settings"),
            ("docs/INVENTORY_ENGINE_SPEC.md", "Inventory Engine Rules", "/reports/reconciliation"),
            ("docs/WARELYN_BUSINESS_WORKFLOW_RBAC_CURRENCY_PLAN.md", "Workflow + RBAC", "/my-tasks"),
        ]
        for rel_path, title, action_to in source_files:
            file_path = root / rel_path
            if not file_path.exists():
                continue
            sources.append(
                {
                    "slug": rel_path.replace("/", "-").replace(".", "-"),
                    "title": title,
                    "source_type": KnowledgeSourceType.DOC,
                    "source_uri": rel_path,
                    "body_text": file_path.read_text(encoding="utf-8"),
                    "metadata_json": {"path": rel_path},
                    "action_to": action_to,
                }
            )
        sources.append(
            {
                "slug": "workflow-task-status-reference",
                "title": "Workflow Task Status Reference",
                "source_type": KnowledgeSourceType.WORKFLOW,
                "source_uri": "internal://workflow-task-status",
                "body_text": (
                    "Workflow task statuses: OPEN means waiting to start, "
                    "IN_PROGRESS means being actively worked, COMPLETED means step done, "
                    "CANCELLED means workflow path no longer valid. "
                    "Order confirmations should produce PICK_ORDER tasks; "
                    "putaway completion should produce RECORD_BILL tasks."
                ),
                "metadata_json": {"scope": "internal"},
                "action_to": "/my-tasks",
            }
        )
        return sources

    def _chunk_text(
        self,
        text: str,
        *,
        source_uri: str | None,
        title: str,
        source_type: str,
        action_to: str | None = None,
    ) -> list[dict[str, Any]]:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks: list[dict[str, Any]] = []
        current = ""
        chunk_index = 0
        for paragraph in paragraphs:
            candidate = f"{current}\n\n{paragraph}".strip()
            if len(candidate) > 1400 and current:
                chunks.append(
                    {
                        "chunk_index": chunk_index,
                        "content": current,
                        "searchable_text": current.lower(),
                        "token_count": len(current.split()),
                        "metadata_json": {
                            "title": title,
                            "source_type": source_type,
                            "source_uri": source_uri,
                            "action_to": action_to,
                        },
                    }
                )
                chunk_index += 1
                current = paragraph
            else:
                current = candidate
        if current:
            chunks.append(
                {
                    "chunk_index": chunk_index,
                    "content": current,
                    "searchable_text": current.lower(),
                    "token_count": len(current.split()),
                    "metadata_json": {
                        "title": title,
                        "source_type": source_type,
                        "source_uri": source_uri,
                        "action_to": action_to,
                    },
                }
            )
        return chunks

    def _retrieve_chunks(self, *, tenant_id: int, question: str) -> list[dict[str, Any]]:
        candidates_limit = self.settings.ai_retrieval_candidates
        keyword_rows = self.repository.search_keyword_chunks(tenant_id=tenant_id, term=question, limit=candidates_limit)
        if not keyword_rows:
            keyword_rows = self.repository.list_recent_chunks(tenant_id=tenant_id, limit=candidates_limit)
        if not keyword_rows:
            return []
        query_embedding = self._embed_one(question)
        scored_rows: list[dict[str, Any]] = []
        for row in keyword_rows:
            lexical = self._lexical_score(question, row.searchable_text)
            semantic = self._cosine_similarity(query_embedding, row.embedding)
            score = (0.45 * lexical) + (0.55 * semantic)
            scored_rows.append({"chunk": row, "score": score})
        scored_rows.sort(key=lambda item: item["score"], reverse=True)
        top_k = self.settings.ai_retrieval_top_k
        return scored_rows[:top_k]

    def _grounded_answer(
        self,
        *,
        question: str,
        context_blocks: list[str],
        mode: str,
        tenant_snapshot: dict[str, Any] | None,
        history: list[AssistantMessage] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        if not context_blocks:
            return (
                {
                    "answer": "I don’t know based on the available knowledge sources.",
                    "confidence": "LOW",
                    "citations": [],
                    "suggested_actions": [{"label": "Open reports overview", "to": "/reports"}],
                    "confidence_score": 0.0,
                },
                {"total_tokens": 0},
            )

        if not self.settings.gemini_api_key:
            top = context_blocks[0][:700]
            return (
                {
                    "answer": f"Based on the current knowledge, here is the most relevant guidance:\n\n{top}",
                    "confidence": "LOW",
                    "citations": [],
                    "suggested_actions": [{"label": "Review source context", "to": "/reports"}],
                    "confidence_score": 0.35,
                },
                {"total_tokens": 0},
            )

        system_prompt = (
            "You are Warelyn Assistant. You must answer only from supplied context. "
            "If evidence is weak, return low confidence and say you do not know. "
            "Never provide hidden/internal secrets and never suggest direct write operations. "
            "Respond strictly as JSON with keys: answer, confidence, confidence_score, suggested_actions."
        )
        user_prompt_parts = [
            f"Mode: {mode}",
            f"Question: {question}",
            "Context:",
            "\n---\n".join(context_blocks),
        ]
        if tenant_snapshot is not None:
            user_prompt_parts.append(f"Tenant snapshot: {json.dumps(tenant_snapshot, default=str)}")
        if history:
            convo = [
                {"role": msg.role, "content": msg.content}
                for msg in history[-6:]
            ]
            user_prompt_parts.append(f"Recent conversation: {json.dumps(convo)}")
        payload = {
            "system_instruction": {
                "parts": [{"text": system_prompt}],
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": "\n\n".join(user_prompt_parts)}],
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json",
            },
        }
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{self.settings.gemini_base_url.rstrip('/')}/models/{self.settings.gemini_chat_model}:generateContent",
                params={"key": self.settings.gemini_api_key},
                json=payload,
            )
        if response.status_code >= 400:
            return (
                {
                    "answer": "I don’t know right now because the assistant provider is unavailable.",
                    "confidence": "LOW",
                    "confidence_score": 0.0,
                    "citations": [],
                    "suggested_actions": [{"label": "Retry later", "to": "/dashboard"}],
                },
                {"total_tokens": 0},
            )
        data = response.json()
        content = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )
        try:
            parsed = json.loads(content) if content else {}
        except json.JSONDecodeError:
            parsed = {}
        usage_meta = data.get("usageMetadata", {})
        usage = {
            "prompt_tokens": int(usage_meta.get("promptTokenCount", 0) or 0),
            "completion_tokens": int(usage_meta.get("candidatesTokenCount", 0) or 0),
            "total_tokens": int(usage_meta.get("totalTokenCount", 0) or 0),
        }
        return parsed, usage

    def _apply_confidence_policy(self, answer_payload: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any]:
        citations = []
        for row in candidates:
            chunk = row["chunk"]
            metadata = chunk.metadata_json or {}
            citations.append(
                {
                    "title": metadata.get("title", "Knowledge Source"),
                    "source_type": metadata.get("source_type", "SYSTEM"),
                    "source_uri": metadata.get("source_uri"),
                    "chunk_id": chunk.id,
                    "score": round(float(row["score"]), 4),
                }
            )
        confidence_score = float(answer_payload.get("confidence_score") or 0.0)
        if confidence_score < self.settings.ai_min_confidence or not citations:
            return {
                "answer": "I don’t know with enough confidence from current sources. Please review the linked references.",
                "confidence": "LOW",
                "confidence_score": confidence_score,
                "citations": citations[:3],
                "suggested_actions": [{"label": "Open reports overview", "to": "/reports"}],
                "abstained": True,
            }

        suggested_actions = []
        for action in answer_payload.get("suggested_actions", []):
            if not isinstance(action, dict):
                continue
            label = str(action.get("label", "")).strip()
            to = str(action.get("to", "")).strip()
            if not label or not to.startswith("/"):
                continue
            suggested_actions.append({"label": label, "to": to})
        if not suggested_actions:
            for citation in citations[:2]:
                if citation.get("source_uri", "").startswith("docs/"):
                    continue
            action_to = (candidates[0]["chunk"].metadata_json or {}).get("action_to")
            if action_to:
                suggested_actions.append({"label": "Open related page", "to": action_to})
        return {
            "answer": str(answer_payload.get("answer") or "").strip() or "I don’t know.",
            "confidence": str(answer_payload.get("confidence") or self._confidence_label(confidence_score)).upper(),
            "confidence_score": confidence_score,
            "citations": citations[:5],
            "suggested_actions": suggested_actions,
            "abstained": False,
        }

    def _audit_event(
        self,
        *,
        tenant_id: int | None,
        actor_user_id: int | None,
        actor_role: str | None,
        action: str,
        entity_type: str | None,
        entity_id: str | None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        try:
            self.audit_repository.create(
                {
                    "tenant_id": tenant_id,
                    "actor_user_id": actor_user_id,
                    "actor_role": actor_role,
                    "action": action,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "metadata_json": metadata or {},
                }
            )
            self.db.commit()
        except Exception:
            self.db.rollback()

    def _context_block(self, row: dict[str, Any]) -> str:
        chunk = row["chunk"]
        metadata = chunk.metadata_json or {}
        header = f"[{metadata.get('title', 'Source')}] score={round(float(row['score']), 4)}"
        return f"{header}\n{chunk.content}"

    def _tenant_admin_snapshot(self, tenant_id: int) -> dict[str, Any]:
        today = datetime.now(UTC).date()
        sales_orders = self.reports_repository.sales_orders(tenant_id)
        purchase_orders = self.reports_repository.purchase_orders(tenant_id)
        low_stock = len(self.reports_repository.stock(tenant_id))
        open_tasks = self.workflow_repository.get_all_tasks(tenant_id, WorkflowTaskStatus.OPEN.value)
        role_counts: dict[str, int] = {}
        for task in open_tasks:
            role_counts[task.assigned_role] = role_counts.get(task.assigned_role, 0) + 1
        return {
            "date": today.isoformat(),
            "open_sales_orders": len([row for row in sales_orders if row.status.value in {"DRAFT", "CONFIRMED", "PARTIALLY_FULFILLED"}]),
            "open_purchase_orders": len([row for row in purchase_orders if row.status.value in {"DRAFT", "SUBMITTED", "PARTIALLY_RECEIVED"}]),
            "open_workflow_tasks_by_role": role_counts,
            "stock_rows_count": low_stock,
        }

    def _embed_many(self, texts: list[str]) -> list[list[float] | None]:
        if not texts:
            return []
        if not self.settings.gemini_api_key:
            return [None for _ in texts]
        vectors: list[list[float] | None] = []
        with httpx.Client(timeout=30.0) as client:
            for text in texts:
                payload = {
                    "model": f"models/{self.settings.gemini_embedding_model}",
                    "content": {"parts": [{"text": text}]},
                }
                response = client.post(
                    f"{self.settings.gemini_base_url.rstrip('/')}/models/{self.settings.gemini_embedding_model}:embedContent",
                    params={"key": self.settings.gemini_api_key},
                    json=payload,
                )
                if response.status_code >= 400:
                    vectors.append(None)
                    continue
                embedding = response.json().get("embedding", {}).get("values")
                vectors.append(embedding if isinstance(embedding, list) else None)
        return vectors

    def _embed_one(self, text: str) -> list[float] | None:
        rows = self._embed_many([text])
        return rows[0] if rows else None

    def _lexical_score(self, question: str, searchable_text: str) -> float:
        q_tokens = [token for token in question.lower().split() if token]
        d_tokens = [token for token in searchable_text.lower().split() if token]
        if not q_tokens or not d_tokens:
            return 0.0
        doc_counts = Counter(d_tokens)
        hits = sum(1 for token in q_tokens if token in doc_counts)
        return min(1.0, hits / max(1, len(set(q_tokens))))

    def _cosine_similarity(self, a: list[float] | None, b: list[float] | None) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b, strict=False))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return max(0.0, min(1.0, dot / (norm_a * norm_b)))

    def _confidence_label(self, score: float) -> str:
        if score >= 0.75:
            return "HIGH"
        if score >= 0.45:
            return "MEDIUM"
        return "LOW"
