import hashlib
import json
import math
import time
from collections import Counter
from datetime import UTC, date, datetime, timedelta
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
    TARGET_CHUNK_SIZE = 600
    OVERLAP_SIZE = 80
    APPLICATION_TERMS = frozenset(
        {
            "warelyn",
            "inventory",
            "stock",
            "warehouse",
            "warehouses",
            "order",
            "orders",
            "sales",
            "purchase",
            "purchasing",
            "return",
            "returns",
            "report",
            "reports",
            "workflow",
            "task",
            "tasks",
            "role",
            "roles",
            "setting",
            "settings",
            "invoice",
            "invoices",
            "bill",
            "bills",
            "receipt",
            "receipts",
            "product",
            "products",
            "vendor",
            "vendors",
            "customer",
            "customers",
            "reconciliation",
            "movement",
            "movements",
            "reorder",
            "batch",
            "batches",
            "expiry",
            "expired",
            "blocked",
            "fulfillment",
            "fulfilment",
            "pick",
            "picking",
            "package",
            "attention",
            "bottleneck",
            "queue",
            "queues",
            "password",
            "user",
            "users",
        }
    )
    REPORT_INTENTS: dict[str, dict[str, str]] = {
        "warehouse stock": {
            "report_type": "warehouse_stock",
            "title": "Warehouse Stock Report",
            "action_url": "/reports/warehouse-stock",
        },
        "stock report": {
            "report_type": "warehouse_stock",
            "title": "Warehouse Stock Report",
            "action_url": "/reports/warehouse-stock",
        },
        "low stock": {
            "report_type": "low_stock",
            "title": "Low Stock Report",
            "action_url": "/reports/low-stock",
        },
        "reorder": {
            "report_type": "reorder_suggestions",
            "title": "Reorder Suggestions",
            "action_url": "/reports/reorder",
        },
        "stock movement": {
            "report_type": "stock_movement",
            "title": "Stock Movement Report",
            "action_url": "/reports/stock-movements",
        },
        "movement report": {
            "report_type": "stock_movement",
            "title": "Stock Movement Report",
            "action_url": "/reports/stock-movements",
        },
        "blocked stock": {
            "report_type": "blocked_stock",
            "title": "Blocked Stock Report",
            "action_url": "/reports/blocked-stock",
        },
        "expir": {
            "report_type": "batch_expiry",
            "title": "Batch Expiry Report",
            "action_url": "/reports/batch-expiry",
        },
        "reconciliation": {
            "report_type": "reconciliation",
            "title": "Reconciliation Report",
            "action_url": "/reports/reconciliation",
        },
        "product valuation": {
            "report_type": "product_valuation",
            "title": "Product Valuation Report",
            "action_url": "/reports/product-valuation",
        },
        "inventory summary": {
            "report_type": "inventory_summary",
            "title": "Inventory Summary",
            "action_url": "/reports/inventory-summary",
        },
        "open orders": {
            "report_type": "open_sales_orders",
            "title": "Open Sales Orders",
            "action_url": "/sales",
        },
        "pending receipts": {
            "report_type": "pending_receipts",
            "title": "Pending Purchase Receipts",
            "action_url": "/purchase-receipts",
        },
        "pending tasks": {
            "report_type": "open_tasks",
            "title": "Open Workflow Tasks",
            "action_url": "/my-tasks",
        },
    }
    REQUIRED_GLOBAL_SOURCE_URIS = {
        "docs/knowledge/WARELYN_WORKFLOW_KNOWLEDGE.md",
        "docs/knowledge/WARELYN_SALES_KNOWLEDGE.md",
        "docs/knowledge/WARELYN_PURCHASE_KNOWLEDGE.md",
        "docs/knowledge/WARELYN_RETURNS_KNOWLEDGE.md",
        "docs/knowledge/WARELYN_INVENTORY_KNOWLEDGE.md",
        "docs/knowledge/WARELYN_ROLES_KNOWLEDGE.md",
        "docs/knowledge/WARELYN_REPORTS_KNOWLEDGE.md",
        "docs/knowledge/WARELYN_FAQ_ANSWERS.md",
    }

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = AssistantRepository(db)
        self.audit_repository = AuditLogRepository(db)
        self.reports_repository = ReportsRepository(db)
        self.workflow_repository = WorkflowRepository(db)
        self.settings = get_settings()

    def ensure_bootstrap_index(self) -> None:
        if self.repository.count_chunks(None) >= 50 and not self._missing_required_global_sources():
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

    def _missing_required_global_sources(self) -> set[str]:
        documents = self.repository.list_documents(None)
        indexed_sources = {document.source_uri for document in documents if document.tenant_id is None}
        return self.REQUIRED_GLOBAL_SOURCE_URIS - indexed_sources

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
        if self._is_off_topic_question(question):
            result = self._off_topic_result()
            result["latency_ms"] = round((time.perf_counter() - started) * 1000, 2)
            result["usage"] = {"total_tokens": 0}
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
                    "abstained": True,
                    "citation_count": 0,
                    "latency_ms": result["latency_ms"],
                    "token_usage": 0,
                    "is_off_topic": True,
                },
            )
            return result
        candidates = self._retrieve_chunks(tenant_id=tenant_id, question=question)
        context_blocks = [self._context_block(row) for row in candidates]
        answer_payload, usage = self._grounded_answer(
            question=question,
            context_blocks=context_blocks,
            mode="faq",
            tenant_snapshot=None,
            role=role,
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
        intent = self._detect_report_intent(question)
        report_filters = self._extract_filters(question, tenant_id) if intent else {}
        report_data = self._fetch_report_data(tenant_id, intent["report_type"], report_filters) if intent else None
        self.repository.create_message(
            tenant_id=tenant_id,
            session_id=session_id,
            user_id=user_id,
            role=AssistantMessageRole.USER.value,
            content=question,
        )
        if self._is_off_topic_question(question) and intent is None:
            result = self._off_topic_result()
            usage = {"total_tokens": 0}
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
                    "abstained": True,
                    "is_off_topic": True,
                    "report_type": None,
                    "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                },
            )
            session.updated_at = datetime.now(UTC)
            self.db.commit()
            self.db.refresh(assistant_message)
            result["message"] = assistant_message
            result["report_data"] = None
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
                    "abstained": True,
                    "citation_count": 0,
                    "token_usage": 0,
                    "is_off_topic": True,
                },
            )
            return result
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
            role=role,
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
                "is_off_topic": bool(result.get("is_off_topic")),
                "report_type": report_data["report_type"] if report_data else None,
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            },
        )
        session.updated_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(assistant_message)
        result["message"] = assistant_message
        result["report_data"] = report_data
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
                "report_type": report_data["report_type"] if report_data else None,
                "is_off_topic": bool(result.get("is_off_topic")),
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
            ("docs/INVENTORY_ENGINE_SPEC.md", "Inventory Engine Rules", KnowledgeSourceType.DOC, "/reports/reconciliation"),
            ("docs/MODULE_BOUNDARIES.md", "Module Boundaries", KnowledgeSourceType.DOC, "/settings"),
            ("docs/knowledge/WARELYN_WORKFLOW_KNOWLEDGE.md", "Workflow Tasks and Status", KnowledgeSourceType.WORKFLOW, "/my-tasks"),
            ("docs/knowledge/WARELYN_SALES_KNOWLEDGE.md", "Sales Order Workflow", KnowledgeSourceType.DOC, "/sales"),
            ("docs/knowledge/WARELYN_PURCHASE_KNOWLEDGE.md", "Purchase Order Workflow", KnowledgeSourceType.DOC, "/purchases"),
            ("docs/knowledge/WARELYN_RETURNS_KNOWLEDGE.md", "Returns and QC Workflow", KnowledgeSourceType.DOC, "/returns"),
            ("docs/knowledge/WARELYN_INVENTORY_KNOWLEDGE.md", "Inventory and Stock Management", KnowledgeSourceType.DOC, "/reports/inventory-summary"),
            ("docs/knowledge/WARELYN_ROLES_KNOWLEDGE.md", "User Roles and Permissions", KnowledgeSourceType.DOC, "/settings/users"),
            ("docs/knowledge/WARELYN_REPORTS_KNOWLEDGE.md", "Reports and Analytics", KnowledgeSourceType.DOC, "/reports"),
            ("docs/knowledge/WARELYN_FAQ_ANSWERS.md", "Frequently Asked Questions", KnowledgeSourceType.DOC, "/faq"),
            # Expanded knowledge base — knowledge_v2
            ("docs/knowledge_v2/WARELYN_TROUBLESHOOTING.md", "Troubleshooting Guide", KnowledgeSourceType.DOC, "/dashboard"),
            ("docs/knowledge_v2/WARELYN_SETTINGS_KNOWLEDGE.md", "Settings and Configuration", KnowledgeSourceType.DOC, "/settings"),
            ("docs/knowledge_v2/WARELYN_PRODUCT_CATALOG_KNOWLEDGE.md", "Product Catalog", KnowledgeSourceType.DOC, "/catalog/products"),
            ("docs/knowledge_v2/WARELYN_WAREHOUSE_KNOWLEDGE.md", "Warehouses and Locations", KnowledgeSourceType.DOC, "/warehouses"),
            ("docs/knowledge_v2/WARELYN_DOCUMENTS_KNOWLEDGE.md", "Invoices and Bills", KnowledgeSourceType.DOC, "/documents"),
            ("docs/knowledge_v2/WARELYN_BATCHES_SERIALS_KNOWLEDGE.md", "Batch and Serial Tracking", KnowledgeSourceType.DOC, "/reports/batch-expiry"),
            ("docs/knowledge_v2/WARELYN_AUDIT_KNOWLEDGE.md", "Audit Logs", KnowledgeSourceType.DOC, "/settings/audit-logs"),
            ("docs/knowledge_v2/WARELYN_NOTIFICATIONS_KNOWLEDGE.md", "Notifications", KnowledgeSourceType.DOC, "/dashboard"),
            ("docs/knowledge_v2/WARELYN_REORDER_KNOWLEDGE.md", "Reorder Rules and Suggestions", KnowledgeSourceType.DOC, "/reports/reorder"),
            ("docs/knowledge_v2/WARELYN_IMPORTS_KNOWLEDGE.md", "Product Import", KnowledgeSourceType.DOC, "/catalog/products/import"),
        ]
        for rel_path, title, source_type, action_to in source_files:
            file_path = root / rel_path
            if not file_path.exists():
                continue
            sources.append(
                {
                    "slug": rel_path.replace("/", "-").replace(".", "-"),
                    "title": title,
                    "source_type": source_type,
                    "source_uri": rel_path,
                    "body_text": file_path.read_text(encoding="utf-8"),
                    "metadata_json": {"path": rel_path},
                    "action_to": action_to,
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
        paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 20]
        chunks = []
        chunk_index = 0
        current = ""

        def emit_content(content: str) -> None:
            nonlocal chunk_index
            content = content.strip()
            while len(content) > self.TARGET_CHUNK_SIZE:
                slice_text = content[: self.TARGET_CHUNK_SIZE].strip()
                chunks.append(self._make_chunk(chunk_index, slice_text, title, source_type, source_uri, action_to))
                chunk_index += 1
                overlap_start = max(0, self.TARGET_CHUNK_SIZE - self.OVERLAP_SIZE)
                content = f"{content[overlap_start:self.TARGET_CHUNK_SIZE]}\n\n{content[self.TARGET_CHUNK_SIZE:]}".strip()
            if content:
                chunks.append(self._make_chunk(chunk_index, content, title, source_type, source_uri, action_to))
                chunk_index += 1

        for paragraph in paragraphs:
            candidate = f"{current}\n\n{paragraph}".strip()
            if len(candidate) > self.TARGET_CHUNK_SIZE and current:
                emit_content(current)
                overlap = current[-self.OVERLAP_SIZE:] if len(current) > self.OVERLAP_SIZE else current
                current = f"{overlap}\n\n{paragraph}".strip()
            else:
                current = candidate

        if current.strip():
            emit_content(current)
        return chunks

    def _make_chunk(
        self,
        index: int,
        content: str,
        title: str,
        source_type: str,
        source_uri: str | None,
        action_to: str | None,
    ) -> dict[str, Any]:
        return {
            "chunk_index": index,
            "content": content,
            "searchable_text": content.lower(),
            "token_count": len(content.split()),
            "metadata_json": {
                "title": title,
                "source_type": source_type,
                "source_uri": source_uri,
                "action_to": action_to,
            },
        }

    def _detect_report_intent(self, question: str) -> dict[str, str] | None:
        q = question.lower()
        for keyword, intent in self.REPORT_INTENTS.items():
            if keyword in q:
                return intent
        return None

    def _is_off_topic_question(self, question: str) -> bool:
        if self._detect_report_intent(question):
            return False
        normalized = " ".join(question.lower().split())
        if "what should i do" in normalized or "what needs my attention" in normalized:
            return False
        tokens = {
            token.strip("?.,!:;\"'()[]{}")
            for token in question.lower().split()
            if token.strip("?.,!:;\"'()[]{}")
        }
        return not bool(tokens & self.APPLICATION_TERMS)

    def _off_topic_result(self) -> dict[str, Any]:
        return {
            "answer": "I can only help with Warelyn Inventory questions.",
            "confidence": "LOW",
            "confidence_score": 0.0,
            "citations": [],
            "suggested_actions": [{"label": "Go to dashboard", "to": "/dashboard"}],
            "abstained": True,
            "is_off_topic": True,
        }

    def _extract_filters(self, question: str, tenant_id: int) -> dict[str, Any]:
        filters: dict[str, Any] = {}
        q = question.lower()
        warehouses = self.reports_repository.warehouses(tenant_id)
        for warehouse in warehouses:
            if warehouse.name.lower() in q:
                filters["warehouse_id"] = warehouse.id
                filters["warehouse_name"] = warehouse.name
                break
        if "today" in q:
            filters["date_from"] = date.today()
            filters["date_to"] = date.today()
        elif "this week" in q or "last 7 days" in q:
            filters["date_from"] = date.today() - timedelta(days=7)
            filters["date_to"] = date.today()
        elif "this month" in q or "last 30 days" in q:
            filters["date_from"] = date.today() - timedelta(days=30)
            filters["date_to"] = date.today()
        if "low stock only" in q or "below reorder" in q:
            filters["low_stock_only"] = True
        return filters

    def _fetch_report_data(self, tenant_id: int, report_type: str, filters: dict[str, Any]) -> dict[str, Any] | None:
        try:
            if report_type == "warehouse_stock":
                return self._report_warehouse_stock(tenant_id, filters)
            if report_type == "low_stock":
                return self._report_low_stock(tenant_id, filters)
            if report_type == "reorder_suggestions":
                return self._report_reorder(tenant_id)
            if report_type == "stock_movement":
                return self._report_stock_movement(tenant_id, filters)
            if report_type == "blocked_stock":
                return self._report_blocked_stock(tenant_id)
            if report_type == "batch_expiry":
                return self._report_batch_expiry(tenant_id)
            if report_type == "reconciliation":
                return self._report_reconciliation(tenant_id)
            if report_type == "open_sales_orders":
                return self._report_open_sales_orders(tenant_id)
            if report_type == "pending_receipts":
                return self._report_pending_receipts(tenant_id)
            if report_type == "open_tasks":
                return self._report_open_tasks(tenant_id)
            if report_type == "inventory_summary":
                return self._report_inventory_summary(tenant_id)
            if report_type == "product_valuation":
                return self._report_product_valuation(tenant_id)
        except Exception:
            return None
        return None

    def _report_warehouse_stock(self, tenant_id: int, filters: dict[str, Any]) -> dict[str, Any]:
        stock_rows = self.reports_repository.stock(tenant_id)
        products = {p.id: p for p in self.reports_repository.products(tenant_id)}
        warehouses = {w.id: w for w in self.reports_repository.warehouses(tenant_id)}
        rows = []
        for stock in stock_rows:
            if filters.get("warehouse_id") and stock.warehouse_id != filters["warehouse_id"]:
                continue
            product = products.get(stock.product_id)
            warehouse = warehouses.get(stock.warehouse_id)
            available = float(stock.quantity_available or 0)
            if filters.get("low_stock_only") and product and float(product.reorder_level or 0) > 0:
                if available >= float(product.reorder_level or 0):
                    continue
            rows.append(
                {
                    "product": product.name if product else f"#{stock.product_id}",
                    "sku": product.sku if product else "",
                    "warehouse": warehouse.name if warehouse else f"#{stock.warehouse_id}",
                    "on_hand": round(float(stock.quantity_on_hand or 0), 2),
                    "reserved": round(float(stock.quantity_reserved or 0), 2),
                    "available": round(available, 2),
                    "reorder_level": float(product.reorder_level or 0) if product else 0,
                }
            )
        rows.sort(key=lambda row: row["available"])
        title = "Warehouse Stock"
        if filters.get("warehouse_name"):
            title = f"{title} - {filters['warehouse_name']}"
        return {
            "report_type": "warehouse_stock",
            "title": title,
            "columns": ["Product", "SKU", "Warehouse", "On Hand", "Reserved", "Available", "Reorder Level"],
            "row_keys": ["product", "sku", "warehouse", "on_hand", "reserved", "available", "reorder_level"],
            "rows": rows[:25],
            "total_rows": len(rows),
            "insights": self._insights_warehouse_stock(rows),
            "action_url": "/reports/warehouse-stock",
        }

    def _insights_warehouse_stock(self, rows: list[dict[str, Any]]) -> list[str]:
        if not rows:
            return ["No stock data found for the selected filters."]
        low_stock = [row for row in rows if row["reorder_level"] > 0 and row["available"] < row["reorder_level"]]
        zero_stock = [row for row in rows if row["available"] <= 0]
        total_available = sum(row["available"] for row in rows)
        insights = [f"{len(rows)} product-warehouse combinations in this view."]
        if zero_stock:
            names = ", ".join(row["product"] for row in zero_stock[:3])
            insights.append(f"{len(zero_stock)} products have zero available stock: {names}{' and more' if len(zero_stock) > 3 else ''}.")
        if low_stock:
            insights.append(f"{len(low_stock)} products are below their reorder level.")
        if total_available > 0:
            highest = max(rows, key=lambda row: row["available"])
            insights.append(f"Highest available: {highest['product']} with {highest['available']} units.")
        return insights

    def _report_low_stock(self, tenant_id: int, filters: dict[str, Any]) -> dict[str, Any]:
        stock_rows = self.reports_repository.stock(tenant_id)
        products = {p.id: p for p in self.reports_repository.products(tenant_id)}
        warehouses = {w.id: w for w in self.reports_repository.warehouses(tenant_id)}
        rows = []
        for stock in stock_rows:
            if filters.get("warehouse_id") and stock.warehouse_id != filters["warehouse_id"]:
                continue
            product = products.get(stock.product_id)
            if not product or not product.reorder_level or float(product.reorder_level) <= 0:
                continue
            available = float(stock.quantity_available or 0)
            if available < float(product.reorder_level):
                warehouse = warehouses.get(stock.warehouse_id)
                rows.append(
                    {
                        "product": product.name,
                        "sku": product.sku or "",
                        "warehouse": warehouse.name if warehouse else f"#{stock.warehouse_id}",
                        "available": round(available, 2),
                        "reorder_level": float(product.reorder_level),
                        "shortage": round(float(product.reorder_level) - available, 2),
                    }
                )
        rows.sort(key=lambda row: row["available"])
        if not rows:
            insights = ["All products are above their reorder levels. Stock health is good."]
        else:
            critical = [row for row in rows if row["available"] <= 0]
            insights = [
                f"{len(rows)} products are below reorder level.",
                f"Total shortage units across all low-stock items: {round(sum(row['shortage'] for row in rows), 2)}.",
            ]
            if critical:
                insights.insert(1, f"{len(critical)} products have zero or negative available stock - urgent action required.")
        return {
            "report_type": "low_stock",
            "title": "Low Stock Report",
            "columns": ["Product", "SKU", "Warehouse", "Available", "Reorder Level", "Shortage"],
            "row_keys": ["product", "sku", "warehouse", "available", "reorder_level", "shortage"],
            "rows": rows[:25],
            "total_rows": len(rows),
            "insights": insights,
            "action_url": "/reports/low-stock",
        }

    def _report_reorder(self, tenant_id: int) -> dict[str, Any]:
        stock_rows = self.reports_repository.stock(tenant_id)
        products = {p.id: p for p in self.reports_repository.products(tenant_id)}
        rows = []
        for stock in stock_rows:
            product = products.get(stock.product_id)
            if not product or not product.reorder_level or float(product.reorder_level) <= 0:
                continue
            available = float(stock.quantity_available or 0)
            if available < float(product.reorder_level):
                rows.append(
                    {
                        "product": product.name,
                        "sku": product.sku or "",
                        "available": round(available, 2),
                        "reorder_level": float(product.reorder_level),
                        "suggested_qty": round(float(product.reorder_level) * 2 - available, 2),
                    }
                )
        rows.sort(key=lambda row: row["available"] - row["reorder_level"])
        return {
            "report_type": "reorder_suggestions",
            "title": "Reorder Suggestions",
            "columns": ["Product", "SKU", "Available", "Reorder Level", "Suggested Order Qty"],
            "row_keys": ["product", "sku", "available", "reorder_level", "suggested_qty"],
            "rows": rows[:25],
            "total_rows": len(rows),
            "insights": [
                f"{len(rows)} products need reordering.",
                "Suggested quantities are 2x the reorder level minus current available stock.",
            ] if rows else ["No products currently need reordering."],
            "action_url": "/purchases/new",
        }

    def _report_stock_movement(self, tenant_id: int, filters: dict[str, Any]) -> dict[str, Any]:
        date_from = filters.get("date_from") or date.today() - timedelta(days=7)
        date_to = filters.get("date_to") or date.today()
        entries = self.reports_repository.ledger(tenant_id, date_from=date_from, date_to=date_to)
        products = {p.id: p for p in self.reports_repository.products(tenant_id)}
        warehouses = {w.id: w for w in self.reports_repository.warehouses(tenant_id)}
        rows = []
        for entry in list(reversed(entries))[-50:]:
            if filters.get("warehouse_id") and entry.warehouse_id != filters["warehouse_id"]:
                continue
            product = products.get(entry.product_id)
            warehouse = warehouses.get(entry.warehouse_id)
            rows.append(
                {
                    "date": entry.created_at.strftime("%Y-%m-%d") if entry.created_at else "",
                    "product": product.name if product else f"#{entry.product_id}",
                    "warehouse": warehouse.name if warehouse else f"#{entry.warehouse_id}",
                    "movement_type": self._enum_value(entry.movement_type),
                    "delta": round(float(entry.quantity_delta or 0), 2),
                    "reference": self._enum_value(entry.reference_type),
                }
            )
        inbound = sum(row["delta"] for row in rows if row["delta"] > 0)
        outbound = sum(row["delta"] for row in rows if row["delta"] < 0)
        return {
            "report_type": "stock_movement",
            "title": f"Stock Movements ({date_from} to {date_to})",
            "columns": ["Date", "Product", "Warehouse", "Type", "Delta", "Reference"],
            "row_keys": ["date", "product", "warehouse", "movement_type", "delta", "reference"],
            "rows": rows,
            "total_rows": len(entries),
            "insights": [
                f"{len(entries)} movements in the selected period.",
                f"Total inbound: +{round(inbound, 2)} units.",
                f"Total outbound: {round(outbound, 2)} units (net: {round(inbound + outbound, 2)}).",
            ],
            "action_url": "/reports/stock-movements",
        }

    def _report_blocked_stock(self, tenant_id: int) -> dict[str, Any]:
        blocked = self.reports_repository.blocked_return_stock(tenant_id)
        products = {p.id: p for p in self.reports_repository.products(tenant_id)}
        rows = []
        for row in blocked:
            product = products.get(row.product_id)
            rows.append(
                {
                    "product": product.name if product else f"#{row.product_id}",
                    "sku": product.sku if product else "",
                    "quantity": round(float(row.quantity or 0), 2),
                    "reason": row.reason or self._enum_value(row.status),
                }
            )
        return {
            "report_type": "blocked_stock",
            "title": "Blocked Stock Report",
            "columns": ["Product", "SKU", "Quantity", "Reason"],
            "row_keys": ["product", "sku", "quantity", "reason"],
            "rows": rows[:25],
            "total_rows": len(rows),
            "insights": [
                f"{len(rows)} blocked stock records.",
                f"Total blocked units: {round(sum(row['quantity'] for row in rows), 2)}.",
            ] if rows else ["No blocked stock found."],
            "action_url": "/reports/blocked-stock",
        }

    def _report_open_sales_orders(self, tenant_id: int) -> dict[str, Any]:
        orders = self.reports_repository.sales_orders(tenant_id)
        customers = {c.id: c for c in self.reports_repository.customers(tenant_id)}
        open_statuses = {"DRAFT", "CONFIRMED", "PARTIALLY_FULFILLED"}
        rows = []
        for order in orders:
            status = self._enum_value(order.status)
            if status not in open_statuses:
                continue
            customer = customers.get(order.customer_id)
            rows.append(
                {
                    "order_number": order.order_number,
                    "customer": customer.name if customer else f"#{order.customer_id}",
                    "status": status,
                    "created_at": order.created_at.strftime("%Y-%m-%d") if order.created_at else "",
                }
            )
        by_status: dict[str, int] = {}
        for row in rows:
            by_status[row["status"]] = by_status.get(row["status"], 0) + 1
        insights = [f"{len(rows)} open sales orders."]
        for status, count in sorted(by_status.items()):
            insights.append(f"{count} in {status}.")
        return {
            "report_type": "open_sales_orders",
            "title": "Open Sales Orders",
            "columns": ["Order Number", "Customer", "Status", "Created"],
            "row_keys": ["order_number", "customer", "status", "created_at"],
            "rows": rows[:25],
            "total_rows": len(rows),
            "insights": insights,
            "action_url": "/sales",
        }

    def _report_pending_receipts(self, tenant_id: int) -> dict[str, Any]:
        receipts = self.reports_repository.purchase_receipts(tenant_id)
        rows = []
        for receipt in receipts:
            status = self._enum_value(receipt.status)
            if status != "DRAFT":
                continue
            rows.append(
                {
                    "receipt_id": receipt.id,
                    "po_id": receipt.purchase_order_id,
                    "status": status,
                    "created_at": receipt.created_at.strftime("%Y-%m-%d") if receipt.created_at else "",
                }
            )
        return {
            "report_type": "pending_receipts",
            "title": "Pending Purchase Receipts",
            "columns": ["Receipt ID", "PO ID", "Status", "Created"],
            "row_keys": ["receipt_id", "po_id", "status", "created_at"],
            "rows": rows[:25],
            "total_rows": len(rows),
            "insights": [f"{len(rows)} pending receipts awaiting commitment."] if rows else ["No pending receipts."],
            "action_url": "/purchase-receipts",
        }

    def _report_open_tasks(self, tenant_id: int) -> dict[str, Any]:
        tasks = self.workflow_repository.get_all_tasks(tenant_id, WorkflowTaskStatus.OPEN.value)
        by_role: dict[str, int] = {}
        rows = []
        for task in tasks[:25]:
            by_role[task.assigned_role] = by_role.get(task.assigned_role, 0) + 1
            rows.append(
                {
                    "title": task.title,
                    "role": task.assigned_role,
                    "step": task.step_key,
                    "priority": task.priority,
                    "created_at": task.created_at.strftime("%Y-%m-%d") if task.created_at else "",
                }
            )
        insights = [f"{len(tasks)} open workflow tasks total."]
        for role, count in sorted(by_role.items(), key=lambda item: -item[1]):
            insights.append(f"{count} tasks for {role.replace('_', ' ').title()}.")
        return {
            "report_type": "open_tasks",
            "title": "Open Workflow Tasks",
            "columns": ["Title", "Assigned Role", "Step", "Priority", "Created"],
            "row_keys": ["title", "role", "step", "priority", "created_at"],
            "rows": rows,
            "total_rows": len(tasks),
            "insights": insights,
            "action_url": "/my-tasks",
        }

    def _report_inventory_summary(self, tenant_id: int) -> dict[str, Any]:
        stock_rows = self.reports_repository.stock(tenant_id)
        products = {p.id: p for p in self.reports_repository.products(tenant_id)}
        total_products = len({stock.product_id for stock in stock_rows})
        total_on_hand = sum(float(stock.quantity_on_hand or 0) for stock in stock_rows)
        total_reserved = sum(float(stock.quantity_reserved or 0) for stock in stock_rows)
        total_available = sum(float(stock.quantity_available or 0) for stock in stock_rows)
        low_stock = sum(
            1
            for stock in stock_rows
            if (product := products.get(stock.product_id))
            and product.reorder_level
            and float(stock.quantity_available or 0) < float(product.reorder_level)
        )
        available_pct = round(total_available / total_on_hand * 100, 1) if total_on_hand else 0
        return {
            "report_type": "inventory_summary",
            "title": "Inventory Summary",
            "columns": ["Metric", "Value"],
            "row_keys": ["metric", "value"],
            "rows": [
                {"metric": "Total SKUs", "value": total_products},
                {"metric": "Total On Hand", "value": round(total_on_hand, 2)},
                {"metric": "Total Reserved", "value": round(total_reserved, 2)},
                {"metric": "Total Available", "value": round(total_available, 2)},
                {"metric": "Low Stock SKUs", "value": low_stock},
            ],
            "total_rows": 5,
            "insights": [
                f"{total_products} SKUs tracked across all warehouses.",
                f"Available stock: {round(total_available, 2)} units ({available_pct}% of on-hand).",
                f"{low_stock} SKUs are below reorder level.",
            ],
            "action_url": "/reports/inventory-summary",
        }

    def _report_batch_expiry(self, tenant_id: int) -> dict[str, Any]:
        batches = self.reports_repository.batches(tenant_id)
        products = {p.id: p for p in self.reports_repository.products(tenant_id)}
        today = date.today()
        warn_date = today + timedelta(days=30)
        rows = []
        for batch in batches:
            if not batch.expiry_date:
                continue
            expiry = batch.expiry_date if isinstance(batch.expiry_date, date) else batch.expiry_date.date()
            if expiry > warn_date:
                continue
            product = products.get(batch.product_id)
            rows.append(
                {
                    "product": product.name if product else f"#{batch.product_id}",
                    "batch": batch.batch_number or f"#{batch.id}",
                    "expiry_date": expiry.isoformat(),
                    "quantity": round(float(batch.quantity_on_hand or 0), 2),
                    "status": "EXPIRED" if expiry < today else "EXPIRING SOON",
                }
            )
        rows.sort(key=lambda row: row["expiry_date"])
        expired = [row for row in rows if row["status"] == "EXPIRED"]
        expiring = [row for row in rows if row["status"] == "EXPIRING SOON"]
        return {
            "report_type": "batch_expiry",
            "title": "Batch Expiry Report (Next 30 Days + Already Expired)",
            "columns": ["Product", "Batch", "Expiry Date", "Quantity", "Status"],
            "row_keys": ["product", "batch", "expiry_date", "quantity", "status"],
            "rows": rows[:25],
            "total_rows": len(rows),
            "insights": [
                f"{len(expired)} batches already expired." if expired else "No expired batches.",
                f"{len(expiring)} batches expiring within 30 days." if expiring else "No batches expiring soon.",
            ],
            "action_url": "/reports/batch-expiry",
        }

    def _report_reconciliation(self, tenant_id: int) -> dict[str, Any]:
        stock_rows = self.reports_repository.stock(tenant_id)
        ledger_entries = self.reports_repository.ledger(tenant_id)
        products = {p.id: p for p in self.reports_repository.products(tenant_id)}
        ledger_totals: dict[tuple[int, int], float] = {}
        for entry in ledger_entries:
            key = (entry.product_id, entry.warehouse_id)
            ledger_totals[key] = ledger_totals.get(key, 0.0) + float(entry.quantity_delta or 0)
        rows = []
        for stock in stock_rows:
            key = (stock.product_id, stock.warehouse_id)
            ledger_qty = round(ledger_totals.get(key, 0.0), 4)
            projection_qty = round(float(stock.quantity_on_hand or 0), 4)
            variance = round(ledger_qty - projection_qty, 4)
            if abs(variance) > 0.001:
                product = products.get(stock.product_id)
                rows.append(
                    {
                        "product": product.name if product else f"#{stock.product_id}",
                        "ledger_qty": ledger_qty,
                        "projection_qty": projection_qty,
                        "variance": variance,
                    }
                )
        return {
            "report_type": "reconciliation",
            "title": "Reconciliation Report",
            "columns": ["Product", "Ledger Qty", "Projection Qty", "Variance"],
            "row_keys": ["product", "ledger_qty", "projection_qty", "variance"],
            "rows": rows[:25],
            "total_rows": len(rows),
            "insights": [
                f"{len(rows)} mismatches found between ledger and projection.",
                "Run the reconciliation process to correct projections." if rows else "",
                "All stock projections are in sync with the ledger." if not rows else "",
            ],
            "action_url": "/reports/reconciliation",
        }

    def _report_product_valuation(self, tenant_id: int) -> dict[str, Any]:
        stock_rows = self.reports_repository.stock(tenant_id)
        products = {p.id: p for p in self.reports_repository.products(tenant_id)}
        rows = []
        for stock in stock_rows:
            product = products.get(stock.product_id)
            if not product:
                continue
            cost = float(product.cost_price or 0)
            quantity = float(stock.quantity_on_hand or 0)
            total_value = round(cost * quantity, 2)
            if total_value > 0:
                rows.append(
                    {
                        "product": product.name,
                        "sku": product.sku or "",
                        "quantity": round(quantity, 2),
                        "cost_price": round(cost, 2),
                        "total_value": total_value,
                    }
                )
        rows.sort(key=lambda row: -row["total_value"])
        total_value = round(sum(row["total_value"] for row in rows), 2)
        return {
            "report_type": "product_valuation",
            "title": "Product Valuation Report",
            "columns": ["Product", "SKU", "Quantity", "Cost Price", "Total Value"],
            "row_keys": ["product", "sku", "quantity", "cost_price", "total_value"],
            "rows": rows[:25],
            "total_rows": len(rows),
            "insights": [
                f"Total inventory value: {total_value}.",
                f"Top product by value: {rows[0]['product']} ({rows[0]['total_value']})." if rows else "",
            ],
            "action_url": "/reports/product-valuation",
        }

    def _enum_value(self, value: Any) -> str:
        return str(value.value if hasattr(value, "value") else value)

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
            score = ((0.45 * lexical) + (0.55 * semantic)) if query_embedding and row.embedding else lexical
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
        role: UserRole | None = None,
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

        role_label = role.value.replace("_", " ").title() if role else "User"
        system_prompt = (
            f"You are Warelyn Inventory Assistant. The user is a {role_label}. "
            "You ONLY answer questions about Warelyn Inventory: stock, orders, warehouses, "
            "purchasing, sales, returns, reports, workflow tasks, user roles, and settings. "
            "If the question is not about inventory management or Warelyn Inventory operations, "
            "respond with: I can only help with Warelyn Inventory questions. "
            "Answer only from the supplied context. "
            "Tailor your answer to what this role can do. "
            "If evidence is weak or context does not cover the question, say you do not know. "
            "Never disclose passwords, tokens, or internal system secrets. "
            "Never suggest executing code, API calls, or database queries directly. "
            "Set confidence_score from your evidence strength, not from the source score shown in context. "
            "Use 0.75-0.95 when the supplied context directly answers the question. "
            "Respond strictly as JSON with keys: "
            "answer (string), confidence (HIGH|MEDIUM|LOW), confidence_score (0.0-1.0), "
            "suggested_actions (list of {label, to}), is_off_topic (bool). "
            "suggested_actions must be an array of objects with label and to keys."
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
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.settings.gemini_base_url.rstrip('/')}/models/{self.settings.gemini_chat_model}:generateContent",
                    params={"key": self.settings.gemini_api_key},
                    json=payload,
                )
        except httpx.HTTPError:
            fallback = self._extractive_fallback_answer(context_blocks, question)
            if fallback:
                return fallback, {"total_tokens": 0}
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
        if response.status_code >= 400:
            fallback = self._extractive_fallback_answer(context_blocks, question)
            if fallback:
                return fallback, {"total_tokens": 0}
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

    def _extractive_fallback_answer(self, context_blocks: list[str], question: str) -> dict[str, Any] | None:
        if not context_blocks:
            return None
        first_block = context_blocks[0]
        header, _, body = first_block.partition("\n")
        score = 0.0
        if "score=" in header:
            try:
                score = float(header.split("score=", 1)[1].strip())
            except ValueError:
                score = 0.0
        if score < 0.65 or not body.strip():
            return None
        excerpt = self._best_faq_excerpt(body.strip(), question)
        return {
            "answer": f"Based on the Warelyn knowledge base:\n\n{excerpt[:900]}",
            "confidence": "HIGH",
            "confidence_score": max(0.72, score),
            "suggested_actions": [{"label": "Open My Tasks", "to": "/my-tasks"}],
        }

    def _best_faq_excerpt(self, body: str, question: str) -> str:
        if "## Q:" not in body:
            return body
        sections = [section.strip() for section in body.split("## Q:") if section.strip()]
        if not sections:
            return body
        best = max(sections, key=lambda section: self._lexical_score(question, section))
        return f"## Q: {best}"

    def _apply_confidence_policy(self, answer_payload: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any]:
        if answer_payload.get("is_off_topic") is True:
            return self._off_topic_result()
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
        confidence_label = str(answer_payload.get("confidence") or "").upper()
        confidence_score = float(answer_payload.get("confidence_score") or 0.0)
        evidence_score = max((float(row["score"]) for row in candidates), default=0.0)
        answer_text = str(answer_payload.get("answer") or "").strip()
        has_substantive_answer = bool(answer_text) and "don’t know" not in answer_text.lower() and "don't know" not in answer_text.lower()
        if citations and has_substantive_answer:
            if confidence_label == "HIGH" and evidence_score >= 0.15:
                confidence_score = max(confidence_score, 0.75, evidence_score)
            elif confidence_label == "MEDIUM" and evidence_score >= self.settings.ai_min_confidence:
                confidence_score = max(confidence_score, 0.55, evidence_score)
            elif evidence_score >= 0.65:
                confidence_score = max(confidence_score, evidence_score)
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
                try:
                    response = client.post(
                        f"{self.settings.gemini_base_url.rstrip('/')}/models/{self.settings.gemini_embedding_model}:embedContent",
                        params={"key": self.settings.gemini_api_key},
                        json=payload,
                    )
                except httpx.HTTPError:
                    vectors.append(None)
                    continue
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
        stop_words = frozenset({
            "how", "do", "i", "a", "an", "the", "is", "are", "what", "why", "when", "where",
            "which", "my", "does", "can", "to", "for", "in", "of", "and", "or", "at", "with",
            "that", "this", "it", "its", "me", "we", "us", "be", "have", "has", "had", "was",
            "were", "will", "would", "could", "should", "may", "might", "not", "no", "get", "got",
        })
        q_tokens = [
            t.strip("?.,!:;\"'()")
            for t in question.lower().split()
            if len(t.strip("?.,!:;\"'()")) > 2 and t.strip("?.,!:;\"'()") not in stop_words
        ]
        d_tokens = [
            token.strip("?.,!:;\"'()")
            for token in searchable_text.lower().split()
            if token.strip("?.,!:;\"'()")
        ]
        if not q_tokens or not d_tokens:
            return 0.0
        k1, b, avg_doc_len = 1.5, 0.75, 150.0
        doc_len = len(d_tokens)
        doc_counts = Counter(d_tokens)
        score = 0.0
        coverage_hits = 0
        for token in set(q_tokens):
            tf = doc_counts.get(token, 0)
            has_fuzzy_match = tf > 0 or any(doc_token.startswith(token) or token.startswith(doc_token) for doc_token in d_tokens)
            if has_fuzzy_match:
                coverage_hits += 1
            if tf == 0:
                continue
            idf = math.log(1.0 + 1.0 / (tf + 0.5))
            tf_norm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * doc_len / avg_doc_len))
            score += idf * tf_norm
        lexical_score = score / max(1, len(set(q_tokens)))
        coverage_score = (coverage_hits / max(1, len(set(q_tokens)))) * 0.85
        return min(1.0, max(lexical_score, coverage_score))

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
