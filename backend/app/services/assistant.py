import hashlib
import json
import math
import time
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.models.assistant import AssistantMessageRole, FAQChunk, KnowledgeSourceType
from app.models.auth import UserRole
from app.models.workflow import WorkflowTaskStatus
from app.repositories.assistant import AssistantRepository
from app.repositories.assistant_mongo import AssistantMongoRepository
from app.repositories.audit import AuditLogRepository
from app.repositories.reports import ReportsRepository
from app.repositories.workflow import WorkflowRepository


@dataclass
class QueryParams:
    limit: int | None = None
    sort_by: str | None = None
    sort_dir: str = "desc"
    warehouse_id: int | None = None
    warehouse_name: str | None = None
    product_id: int | None = None
    product_name: str | None = None
    category_id: int | None = None
    category_name: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    max_available: float | None = None
    min_available: float | None = None
    low_stock_only: bool = False
    movement_type: str | None = None
    status_filter: str | None = None
    entity_focus: str | None = None


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
    WORKFLOW_INTENTS = {
        "draft a workflow",
        "create a workflow",
        "design a workflow",
        "plan a workflow",
        "workflow for",
        "process for",
        "steps to",
        "how should i handle",
    }
    WORKFLOW_ACTION_KEYWORDS = {
        "draft",
        "create",
        "prepare",
        "make",
        "raise",
        "generate",
        "need",
        "plan",
        "outline",
        "build",
        "guide",
        "help",
    }
    WORKFLOW_ALIASES = {
        "purchase order": ("purchase order", " po "),
        "sales order": ("sales order", " so "),
        "sales return": ("sales return", " return "),
        "cycle count": ("cycle count", "stock count", "count session"),
    }
    WORKFLOW_TEMPLATES: dict[str, list[dict[str, Any]]] = {
        "purchase order": [
            {"step": 1, "action": "Create purchase order", "role": "PURCHASE_STAFF", "status_change": "DRAFT -> SUBMITTED", "task_created": None, "note": "Set vendor, items, quantities, expected delivery."},
            {"step": 2, "action": "High-value approval if required", "role": "TENANT_ADMIN", "status_change": None, "task_created": "APPROVE_PO", "note": "Triggered for orders above the approval threshold."},
            {"step": 3, "action": "Receive stock from vendor", "role": "INVENTORY_MANAGER", "status_change": "SUBMITTED -> PARTIALLY_RECEIVED", "task_created": "PUTAWAY_STOCK", "note": "Commit purchase receipt for actual delivered quantities."},
            {"step": 4, "action": "Putaway stock in warehouse locations", "role": "INVENTORY_MANAGER", "status_change": "Putaway PENDING -> COMPLETED", "task_created": "RECORD_BILL", "note": "Place received items in the correct warehouse locations."},
            {"step": 5, "action": "Record vendor bill", "role": "PURCHASE_STAFF", "status_change": "Bill DRAFT -> RECORDED", "task_created": None, "note": "Match bill to the PO and receipt, set due date, and track payment."},
        ],
        "sales order": [
            {"step": 1, "action": "Create sales order", "role": "SALES_STAFF", "status_change": "DRAFT", "task_created": None, "note": "Add customer, product lines, and quantities."},
            {"step": 2, "action": "Confirm sales order", "role": "SALES_STAFF", "status_change": "DRAFT -> CONFIRMED", "task_created": "PICK_ORDER", "note": "Reserves stock. The order cannot be freely edited after confirmation."},
            {"step": 3, "action": "Pick items from warehouse", "role": "INVENTORY_MANAGER", "status_change": None, "task_created": None, "note": "Physically pick products from reserved warehouse locations."},
            {"step": 4, "action": "Pack items into package", "role": "INVENTORY_MANAGER", "status_change": None, "task_created": None, "note": "Create package and assign picked items."},
            {"step": 5, "action": "Commit fulfillment", "role": "INVENTORY_MANAGER", "status_change": "CONFIRMED -> FULFILLED", "task_created": "CREATE_INVOICE", "note": "Deducts reserved stock and updates order status."},
            {"step": 6, "action": "Create and send invoice", "role": "SALES_STAFF", "status_change": "Invoice DRAFT -> SENT", "task_created": None, "note": "Send the invoice PDF to the customer by email."},
        ],
        "sales return": [
            {"step": 1, "action": "Create return", "role": "SALES_STAFF", "status_change": "DRAFT", "task_created": None, "note": "Select fulfilled order, returned quantities, and reason."},
            {"step": 2, "action": "Submit return", "role": "SALES_STAFF", "status_change": "DRAFT -> SUBMITTED", "task_created": "RETURN_QC", "note": "Creates a QC task for the warehouse team."},
            {"step": 3, "action": "QC inspection", "role": "INVENTORY_MANAGER", "status_change": "SUBMITTED -> INSPECTION_PENDING", "task_created": None, "note": "Assign outcome per item: ACCEPTED_RESTOCK, DAMAGED, SCRAPPED, or REJECTED."},
            {"step": 4, "action": "Process return", "role": "INVENTORY_MANAGER", "status_change": "INSPECTION_PENDING -> PROCESSED", "task_created": None, "note": "Applies stock changes based on QC decisions."},
        ],
        "cycle count": [
            {"step": 1, "action": "Create count session", "role": "INVENTORY_MANAGER", "status_change": "DRAFT", "task_created": None, "note": "Select warehouse and products to count."},
            {"step": 2, "action": "Physically count items", "role": "INVENTORY_MANAGER", "status_change": "DRAFT -> IN_PROGRESS", "task_created": None, "note": "Enter counted quantities for each product."},
            {"step": 3, "action": "Submit session", "role": "INVENTORY_MANAGER", "status_change": "IN_PROGRESS -> SUBMITTED", "task_created": None, "note": "System calculates variance between counted and system quantity."},
            {"step": 4, "action": "Review variances", "role": "INVENTORY_MANAGER", "status_change": None, "task_created": None, "note": "Check each mismatch before reconciling."},
            {"step": 5, "action": "Reconcile", "role": "INVENTORY_MANAGER", "status_change": "SUBMITTED -> RECONCILED", "task_created": None, "note": "System adjusts stock to match the physical count."},
        ],
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
        "docs/knowledge/WARELYN_TROUBLESHOOTING.md",
        "docs/knowledge/WARELYN_SETTINGS_KNOWLEDGE.md",
        "docs/knowledge/WARELYN_PRODUCT_CATALOG_KNOWLEDGE.md",
        "docs/knowledge/WARELYN_WAREHOUSE_KNOWLEDGE.md",
        "docs/knowledge/WARELYN_DOCUMENTS_KNOWLEDGE.md",
        "docs/knowledge/WARELYN_BATCHES_SERIALS_KNOWLEDGE.md",
        "docs/knowledge/WARELYN_AUDIT_KNOWLEDGE.md",
        "docs/knowledge/WARELYN_NOTIFICATIONS_KNOWLEDGE.md",
        "docs/knowledge/WARELYN_REORDER_KNOWLEDGE.md",
        "docs/knowledge/WARELYN_IMPORTS_KNOWLEDGE.md",
        "docs/knowledge_v2/WARELYN_ENTITY_RELATIONSHIPS.md",
        "docs/knowledge_v2/WARELYN_API_ENDPOINT_MAP.md",
        "docs/knowledge_v2/WARELYN_MODULE_ARCHITECTURE.md",
        "docs/knowledge_v2/WARELYN_FRONTEND_ARCHITECTURE.md",
    }

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = AssistantRepository(db)
        self.mongo_repo = AssistantMongoRepository()
        self.audit_repository = AuditLogRepository(db)
        self.reports_repository = ReportsRepository(db)
        self.workflow_repository = WorkflowRepository(db)
        self.settings = get_settings()

    def ensure_bootstrap_index(self) -> None:
        if self.repository.count_chunks(None) >= 100 and not self._missing_required_global_sources():
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

    def create_session(self, *, tenant_id: int, user_id: int, title: str | None = None) -> dict:
        session = self.mongo_repo.create_session(
            tenant_id=tenant_id,
            user_id=user_id,
            title=title or "New Assistant Session",
        )
        self._audit_event(
            tenant_id=tenant_id,
            actor_user_id=user_id,
            actor_role=UserRole.TENANT_ADMIN.value,
            action="ASSISTANT_SESSION_CREATE",
            entity_type="assistant_session",
            entity_id=str(session["id"]),
            metadata={"title": session["title"]},
        )
        return session

    def get_session_detail(self, *, tenant_id: int, user_id: int, session_id: int) -> dict[str, Any]:
        session = self.mongo_repo.get_session(tenant_id=tenant_id, session_id=session_id)
        if session is None or session["user_id"] != user_id:
            raise AppError("ASSISTANT_SESSION_NOT_FOUND", "Assistant session not found.", 404)
        messages = self.mongo_repo.list_messages(tenant_id=tenant_id, session_id=session_id)
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
        session = self.mongo_repo.get_session(tenant_id=tenant_id, session_id=session_id)
        if session is None or session["user_id"] != user_id:
            raise AppError("ASSISTANT_SESSION_NOT_FOUND", "Assistant session not found.", 404)

        if self.mongo_repo.count_messages(tenant_id=tenant_id, session_id=session_id) == 0:
            title = question[:80].rstrip()
            self.mongo_repo.update_session_title(session_id, title)

        started = time.perf_counter()
        intent = self._detect_report_intent(question)
        query_params = self._parse_query_params(question, tenant_id) if intent else QueryParams()
        report_data = self._fetch_report_data(tenant_id, intent["report_type"], query_params) if intent else None
        workflow_data = self._draft_workflow(question, tenant_id) if self._detect_workflow_intent(question) else None
        self.mongo_repo.create_message(
            tenant_id=tenant_id,
            session_id=session_id,
            user_id=user_id,
            role=AssistantMessageRole.USER.value,
            content=question,
        )
        if self._is_off_topic_question(question) and intent is None and workflow_data is None:
            result = self._off_topic_result()
            usage = {"total_tokens": 0}
            assistant_message = self.mongo_repo.create_message(
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
            self.mongo_repo.update_session_timestamp(session_id)
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
        if workflow_data is not None:
            result = {
                "answer": self._workflow_answer(workflow_data),
                "confidence": "HIGH",
                "confidence_score": 0.9,
                "citations": [],
                "suggested_actions": [self._workflow_action(workflow_data)],
                "abstained": False,
                "is_off_topic": False,
            }
            usage = {"total_tokens": 0}
            assistant_message = self.mongo_repo.create_message(
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
                    "abstained": False,
                    "is_off_topic": False,
                    "report_type": workflow_data["report_type"],
                    "report_data": workflow_data,
                    "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                },
            )
            self.mongo_repo.update_session_timestamp(session_id)
            result["message"] = assistant_message
            result["report_data"] = workflow_data
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
                    "abstained": False,
                    "citation_count": 0,
                    "token_usage": 0,
                    "report_type": workflow_data["report_type"],
                    "is_off_topic": False,
                },
            )
            return result
        history = self.mongo_repo.list_messages(tenant_id=tenant_id, session_id=session_id)[-8:]
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
        assistant_message = self.mongo_repo.create_message(
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
                "report_type": (report_data or workflow_data)["report_type"] if (report_data or workflow_data) else None,
                "report_data": report_data or workflow_data,
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            },
        )
        self.mongo_repo.update_session_timestamp(session_id)
        result["message"] = assistant_message
        result["report_data"] = report_data or workflow_data
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
                "report_type": (report_data or workflow_data)["report_type"] if (report_data or workflow_data) else None,
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
        message = self.mongo_repo.get_message(tenant_id=tenant_id, message_id=message_id)
        if message is None:
            raise AppError("ASSISTANT_MESSAGE_NOT_FOUND", "Assistant message was not found.", 404)
        feedback = self.mongo_repo.upsert_feedback(
            tenant_id=tenant_id,
            message_id=message_id,
            user_id=user_id,
            value=value,
            note=note,
        )
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

    def delete_session(self, *, tenant_id: int, user_id: int, session_id: int) -> None:
        session = self.mongo_repo.get_session(tenant_id=tenant_id, session_id=session_id)
        if session is None or session["user_id"] != user_id:
            raise AppError("ASSISTANT_SESSION_NOT_FOUND", "Assistant session not found.", 404)
        self.mongo_repo.delete_session(tenant_id=tenant_id, session_id=session_id)
        self._audit_event(
            tenant_id=tenant_id,
            actor_user_id=user_id,
            actor_role=UserRole.TENANT_ADMIN.value,
            action="ASSISTANT_SESSION_DELETE",
            entity_type="assistant_session",
            entity_id=str(session_id),
        )

    def list_sessions(self, *, tenant_id: int, user_id: int) -> list[dict]:
        return self.mongo_repo.list_sessions_for_user(tenant_id=tenant_id, user_id=user_id)

    def telemetry(self, *, tenant_id: int) -> dict[str, Any]:
        return self.mongo_repo.get_telemetry(tenant_id=tenant_id)

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
            ("docs/knowledge/WARELYN_TROUBLESHOOTING.md", "Troubleshooting Guide", KnowledgeSourceType.DOC, "/dashboard"),
            ("docs/knowledge/WARELYN_SETTINGS_KNOWLEDGE.md", "Settings and Configuration", KnowledgeSourceType.DOC, "/settings"),
            ("docs/knowledge/WARELYN_PRODUCT_CATALOG_KNOWLEDGE.md", "Product Catalog", KnowledgeSourceType.DOC, "/catalog/products"),
            ("docs/knowledge/WARELYN_WAREHOUSE_KNOWLEDGE.md", "Warehouses and Locations", KnowledgeSourceType.DOC, "/warehouses"),
            ("docs/knowledge/WARELYN_DOCUMENTS_KNOWLEDGE.md", "Invoices and Bills", KnowledgeSourceType.DOC, "/documents"),
            ("docs/knowledge/WARELYN_BATCHES_SERIALS_KNOWLEDGE.md", "Batch and Serial Tracking", KnowledgeSourceType.DOC, "/reports/batch-expiry"),
            ("docs/knowledge/WARELYN_AUDIT_KNOWLEDGE.md", "Audit Logs", KnowledgeSourceType.DOC, "/settings/audit-logs"),
            ("docs/knowledge/WARELYN_NOTIFICATIONS_KNOWLEDGE.md", "Notifications", KnowledgeSourceType.DOC, "/dashboard"),
            ("docs/knowledge/WARELYN_REORDER_KNOWLEDGE.md", "Reorder Rules and Suggestions", KnowledgeSourceType.DOC, "/reports/reorder"),
            ("docs/knowledge/WARELYN_IMPORTS_KNOWLEDGE.md", "Product Import", KnowledgeSourceType.DOC, "/catalog/products/import"),
            ("docs/knowledge_v2/WARELYN_ENTITY_RELATIONSHIPS.md", "Entity Relationships and Architecture", KnowledgeSourceType.DOC, "/dashboard"),
            ("docs/knowledge_v2/WARELYN_API_ENDPOINT_MAP.md", "API Endpoint Reference", KnowledgeSourceType.DOC, "/settings"),
            ("docs/knowledge_v2/WARELYN_MODULE_ARCHITECTURE.md", "Backend Module Architecture", KnowledgeSourceType.DOC, "/dashboard"),
            ("docs/knowledge_v2/WARELYN_FRONTEND_ARCHITECTURE.md", "Frontend Architecture", KnowledgeSourceType.DOC, "/dashboard"),
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

    def _detect_workflow_intent(self, question: str) -> bool:
        q = question.lower()
        if any(keyword in q for keyword in self.WORKFLOW_INTENTS):
            return True
        if self._match_workflow_name(question) and any(keyword in q for keyword in self.WORKFLOW_ACTION_KEYWORDS):
            return True
        return "workflow" in q and any(
            keyword in q
            for keyword in ["draft", "create", "design", "plan", "outline", "build"]
        )

    def _match_workflow_name(self, question: str) -> str | None:
        q = f" {question.lower()} "
        for name in ["sales return", "purchase order", "sales order", "cycle count"]:
            aliases = self.WORKFLOW_ALIASES[name]
            if any(alias in q for alias in aliases):
                return name
        return None

    def _draft_workflow(self, question: str, tenant_id: int) -> dict[str, Any] | None:
        matched_name = self._match_workflow_name(question)
        matched_template = self.WORKFLOW_TEMPLATES.get(matched_name or "")
        if not matched_name or not matched_template:
            return None
        detail_builders = {
            "purchase order": self._draft_purchase_order,
            "sales order": self._draft_sales_order,
            "sales return": self._draft_sales_return,
            "cycle count": self._draft_cycle_count,
        }
        detail_draft = detail_builders[matched_name](question)
        if detail_draft:
            return detail_draft
        return {
            "report_type": "workflow_draft",
            "workflow_type": "draft",
            "workflow_name": matched_name.title(),
            "title": f"{matched_name.title()} Workflow Draft",
            "columns": ["Step", "Action", "Role", "Status Change", "Task Created", "Notes"],
            "row_keys": ["step", "action", "role", "status_change", "task_created", "note"],
            "rows": matched_template,
            "total_rows": len(matched_template),
            "insights": [
                f"This is the standard Warelyn workflow for {matched_name}.",
                "Each task listed in 'Task Created' appears automatically in My Tasks for the assigned role.",
                "Roles can only see and act on tasks assigned to their role.",
            ],
            "action_url": "/my-tasks",
            "query_summary": f"Workflow draft: {matched_name.title()}",
        }

    def _find_labeled_field(self, question: str, label: str, labels: str) -> str | None:
        import re

        match = re.search(
            rf"\b{re.escape(label)}:\s*(.+?)(?=\s+-\s+(?:{labels}):|$)",
            question,
            flags=re.IGNORECASE,
        )
        return match.group(1).strip(" .,-") if match else None

    def _find_pattern(self, question: str, pattern: str) -> str | None:
        import re

        match = re.search(pattern, question, flags=re.IGNORECASE)
        return match.group(1).strip(" .,-") if match else None

    def _draft_purchase_order(self, question: str) -> dict[str, Any] | None:
        labels = "Product|SKU|Quantity|Vendor|Warehouse|Expected delivery date|Unit cost|Notes"

        quantity = self._find_pattern(question, r"\b(\d+(?:\.\d+)?)\s*(?:units?|pcs|pieces?)\b")
        product = self._find_pattern(question, r"(?:units?|pcs|pieces?)\s+of\s+(.+?)(?:\s+from\s+|\.|$)")
        vendor = self._find_pattern(question, r"\bfrom\s+(.+?)(?:\.|$|use these field details| - )")
        explicit_product = self._find_labeled_field(question, "Product", labels)
        sku = self._find_labeled_field(question, "SKU", labels)
        explicit_quantity = self._find_labeled_field(question, "Quantity", labels)
        explicit_vendor = self._find_labeled_field(question, "Vendor", labels)
        warehouse = self._find_labeled_field(question, "Warehouse", labels)
        expected_delivery = self._find_labeled_field(question, "Expected delivery date", labels)
        unit_cost = self._find_labeled_field(question, "Unit cost", labels)
        notes = self._find_labeled_field(question, "Notes", labels)

        product = explicit_product or product
        quantity = explicit_quantity or quantity
        vendor = explicit_vendor or vendor

        if not product and not quantity and not vendor:
            return None

        rows = [
            {"field": "Product", "draft_value": product or "Missing", "required": "Yes", "where_to_check": "Catalog > Products", "note": "Choose the exact active product record before submitting."},
            {"field": "SKU", "draft_value": sku or "Confirm in product selector", "required": "Recommended", "where_to_check": "Catalog > Products", "note": "SKU helps avoid choosing a similarly named item."},
            {"field": "Quantity", "draft_value": quantity or "Missing", "required": "Yes", "where_to_check": "Purchase order line item", "note": "Enter the purchase quantity for this product."},
            {"field": "Vendor", "draft_value": vendor or "Missing", "required": "Yes", "where_to_check": "Catalog > Vendors", "note": "Select the vendor that supplies this item."},
            {"field": "Warehouse", "draft_value": warehouse or "Choose receiving warehouse", "required": "Yes", "where_to_check": "Warehouses", "note": "This is where the purchase receipt will be received."},
            {"field": "Expected delivery date", "draft_value": expected_delivery or "Add expected delivery date", "required": "Recommended", "where_to_check": "Purchase order header", "note": "Expected date should not be earlier than the PO creation date."},
            {"field": "Unit cost", "draft_value": unit_cost or "Confirm latest vendor cost", "required": "Yes", "where_to_check": "Purchase order line item", "note": "Used to calculate PO total and later bill matching."},
            {"field": "Notes", "draft_value": notes or "Optional", "required": "No", "where_to_check": "Purchase order notes", "note": "Useful for reorder reason or approval context."},
        ]
        missing = [row["field"] for row in rows if row["draft_value"] == "Missing"]
        return {
            "report_type": "purchase_order_draft",
            "workflow_type": "draft",
            "workflow_name": "Purchase Order",
            "title": "Purchase Order Draft",
            "columns": ["Field", "Draft Value", "Required", "Where To Check", "Note"],
            "row_keys": ["field", "draft_value", "required", "where_to_check", "note"],
            "rows": rows,
            "total_rows": len(rows),
            "insights": [
                "This is a read-only copilot draft; it has not created a PO in the database.",
                "Open the purchase order form and copy these values into the header and line item fields.",
                f"Missing required fields: {', '.join(missing)}." if missing else "All core required PO draft fields are present.",
                "After submit, the purchase workflow moves through approval if needed, receipt, putaway, and bill recording.",
            ],
            "action_url": "/purchases/new",
            "query_summary": f"Draft PO for {quantity or '?'} units of {product or 'selected product'}",
        }

    def _draft_sales_order(self, question: str) -> dict[str, Any] | None:
        labels = "Customer|Product|SKU|Quantity|Warehouse|Expected ship date|Expected delivery date|Unit price|Notes"
        quantity = self._find_labeled_field(question, "Quantity", labels) or self._find_pattern(
            question,
            r"\b(\d+(?:\.\d+)?)\s*(?:units?|pcs|pieces?)\b",
        )
        product = self._find_labeled_field(question, "Product", labels) or self._find_pattern(
            question,
            r"(?:units?|pcs|pieces?)\s+of\s+(.+?)(?:\s+for\s+customer\s+|\.|$)",
        )
        customer = self._find_labeled_field(question, "Customer", labels) or self._find_pattern(
            question,
            r"\bfor\s+customer\s+(.+?)(?:\.|$| - )",
        )
        sku = self._find_labeled_field(question, "SKU", labels)
        warehouse = self._find_labeled_field(question, "Warehouse", labels)
        expected_ship = (
            self._find_labeled_field(question, "Expected ship date", labels)
            or self._find_labeled_field(question, "Expected delivery date", labels)
        )
        unit_price = self._find_labeled_field(question, "Unit price", labels)
        notes = self._find_labeled_field(question, "Notes", labels)
        if not product and not quantity and not customer:
            return None

        rows = [
            {"field": "Customer", "draft_value": customer or "Missing", "required": "Yes", "where_to_check": "Catalog > Customers", "note": "Choose the customer placing this order."},
            {"field": "Product", "draft_value": product or "Missing", "required": "Yes", "where_to_check": "Catalog > Products", "note": "Choose the exact product to sell."},
            {"field": "SKU", "draft_value": sku or "Confirm in product selector", "required": "Recommended", "where_to_check": "Catalog > Products", "note": "SKU helps avoid choosing a similarly named product."},
            {"field": "Quantity", "draft_value": quantity or "Missing", "required": "Yes", "where_to_check": "Sales order line item", "note": "Enter the customer ordered quantity."},
            {"field": "Warehouse", "draft_value": warehouse or "Choose fulfillment warehouse", "required": "Recommended", "where_to_check": "Sales order allocation / pick flow", "note": "Stock reservation and picking use warehouse availability."},
            {"field": "Expected ship date", "draft_value": expected_ship or "Add expected ship date", "required": "Recommended", "where_to_check": "Sales order header or notes", "note": "Use a date that reflects customer commitment."},
            {"field": "Unit price", "draft_value": unit_price or "Confirm sales price", "required": "Yes", "where_to_check": "Sales order line item", "note": "Used for the sales order and later invoice."},
            {"field": "Notes", "draft_value": notes or "Optional", "required": "No", "where_to_check": "Sales order notes", "note": "Add delivery promise, customer reference, or constraints."},
        ]
        missing = [row["field"] for row in rows if row["draft_value"] == "Missing"]
        return {
            "report_type": "sales_order_draft",
            "workflow_type": "draft",
            "workflow_name": "Sales Order",
            "title": "Sales Order Draft",
            "columns": ["Field", "Draft Value", "Required", "Where To Check", "Note"],
            "row_keys": ["field", "draft_value", "required", "where_to_check", "note"],
            "rows": rows,
            "total_rows": len(rows),
            "insights": [
                "This is a read-only copilot draft; it has not created a sales order in the database.",
                "Open the sales order form and copy these values into the header and line item fields.",
                f"Missing required fields: {', '.join(missing)}." if missing else "All core required SO draft fields are present.",
                "After confirmation, Warelyn reserves stock and creates a PICK_ORDER task for inventory.",
            ],
            "action_url": "/sales/new",
            "query_summary": f"Draft SO for {quantity or '?'} units of {product or 'selected product'}",
        }

    def _draft_sales_return(self, question: str) -> dict[str, Any] | None:
        labels = "Sales order|Return number|Customer|Product|SKU|Returned quantity|Quantity|Warehouse|Location|Reason|Notes"
        sales_order = self._find_labeled_field(question, "Sales order", labels) or self._find_pattern(
            question,
            r"\b(?:sales order|so)\s+#?\s*([A-Za-z0-9_-]+)\b",
        )
        return_number = self._find_labeled_field(question, "Return number", labels)
        customer = self._find_labeled_field(question, "Customer", labels)
        product = self._find_labeled_field(question, "Product", labels) or self._find_pattern(
            question,
            r"(?:return|returned)\s+\d+(?:\.\d+)?\s*(?:units?|pcs|pieces?)\s+of\s+(.+?)(?:\s+from\s+|\.|$)",
        )
        sku = self._find_labeled_field(question, "SKU", labels)
        quantity = (
            self._find_labeled_field(question, "Returned quantity", labels)
            or self._find_labeled_field(question, "Quantity", labels)
            or self._find_pattern(question, r"\b(\d+(?:\.\d+)?)\s*(?:units?|pcs|pieces?)\b")
        )
        warehouse = self._find_labeled_field(question, "Warehouse", labels)
        location = self._find_labeled_field(question, "Location", labels)
        reason = self._find_labeled_field(question, "Reason", labels)
        notes = self._find_labeled_field(question, "Notes", labels)
        if not sales_order and not product and not quantity and not reason:
            return None

        rows = [
            {"field": "Sales order", "draft_value": sales_order or "Missing", "required": "Yes", "where_to_check": "Sales > Sales order detail", "note": "Returns must link to the fulfilled sales order."},
            {"field": "Return number", "draft_value": return_number or "Auto-generate or enter manually", "required": "Recommended", "where_to_check": "Return header", "note": "Use a unique return reference."},
            {"field": "Customer", "draft_value": customer or "Confirm from sales order", "required": "Derived", "where_to_check": "Sales order detail", "note": "Customer is normally tied to the selected sales order."},
            {"field": "Product", "draft_value": product or "Select returned product", "required": "Yes", "where_to_check": "Return line item", "note": "Only products from the fulfilled order should be returned."},
            {"field": "SKU", "draft_value": sku or "Confirm in product selector", "required": "Recommended", "where_to_check": "Return line item", "note": "SKU avoids selecting a similarly named item."},
            {"field": "Returned quantity", "draft_value": quantity or "Missing", "required": "Yes", "where_to_check": "Return line item", "note": "Cannot exceed fulfilled quantity."},
            {"field": "Warehouse", "draft_value": warehouse or "Choose receiving/QC warehouse", "required": "Yes", "where_to_check": "Returns form", "note": "Returned stock routes to QC or blocked stock handling."},
            {"field": "Location", "draft_value": location or "Choose QC/return location", "required": "Recommended", "where_to_check": "Returns form", "note": "Useful when returns are inspected at a specific bin."},
            {"field": "Reason", "draft_value": reason or "Missing", "required": "Yes", "where_to_check": "Return header or line", "note": "Reason helps QC decide restock, block, scrap, or reject."},
            {"field": "Notes", "draft_value": notes or "Optional", "required": "No", "where_to_check": "Return notes", "note": "Add customer explanation or inspection hints."},
        ]
        missing = [row["field"] for row in rows if row["draft_value"] == "Missing"]
        return {
            "report_type": "sales_return_draft",
            "workflow_type": "draft",
            "workflow_name": "Sales Return",
            "title": "Sales Return Draft",
            "columns": ["Field", "Draft Value", "Required", "Where To Check", "Note"],
            "row_keys": ["field", "draft_value", "required", "where_to_check", "note"],
            "rows": rows,
            "total_rows": len(rows),
            "insights": [
                "This is a read-only copilot draft; it has not created a return in the database.",
                "Open the return form and copy these values into the return header and line item fields.",
                f"Missing required fields: {', '.join(missing)}." if missing else "All core required return draft fields are present.",
                "After submission, Warelyn creates a RETURN_QC task for inventory inspection.",
            ],
            "action_url": "/returns/new",
            "query_summary": f"Draft return for {quantity or '?'} units from {sales_order or 'selected sales order'}",
        }

    def _draft_cycle_count(self, question: str) -> dict[str, Any] | None:
        labels = "Session name|Warehouse|Location|Products|Product|Category|Scheduled date|Reason|Notes"
        session_name = self._find_labeled_field(question, "Session name", labels)
        warehouse = self._find_labeled_field(question, "Warehouse", labels)
        location = self._find_labeled_field(question, "Location", labels)
        products = (
            self._find_labeled_field(question, "Products", labels)
            or self._find_labeled_field(question, "Product", labels)
            or self._find_pattern(question, r"\bcount\s+(.+?)(?:\s+in\s+|\.|$)")
        )
        category = self._find_labeled_field(question, "Category", labels)
        scheduled_date = self._find_labeled_field(question, "Scheduled date", labels)
        reason = self._find_labeled_field(question, "Reason", labels)
        notes = self._find_labeled_field(question, "Notes", labels)
        if not warehouse and not products and not category and not reason:
            return None

        rows = [
            {"field": "Session name", "draft_value": session_name or "Auto-generate or enter manually", "required": "Recommended", "where_to_check": "Cycle count session header", "note": "Use a name that explains the count scope."},
            {"field": "Warehouse", "draft_value": warehouse or "Missing", "required": "Yes", "where_to_check": "Warehouses", "note": "Cycle count sessions are scoped to a warehouse."},
            {"field": "Location", "draft_value": location or "Optional / all locations", "required": "No", "where_to_check": "Warehouse locations", "note": "Use a location when the count is bin-specific."},
            {"field": "Products", "draft_value": products or "Select products after session creation", "required": "Yes", "where_to_check": "Cycle count lines", "note": "Add each product you want physically counted."},
            {"field": "Category", "draft_value": category or "Optional", "required": "No", "where_to_check": "Catalog > Categories", "note": "Category helps define a focused count scope."},
            {"field": "Scheduled date", "draft_value": scheduled_date or "Add planned count date", "required": "Recommended", "where_to_check": "Cycle count notes", "note": "Use this to coordinate warehouse work."},
            {"field": "Reason", "draft_value": reason or "Optional", "required": "No", "where_to_check": "Cycle count notes", "note": "Examples: reconciliation mismatch, audit check, low stock verification."},
            {"field": "Notes", "draft_value": notes or "Optional", "required": "No", "where_to_check": "Cycle count notes", "note": "Add instructions for counters."},
        ]
        missing = [row["field"] for row in rows if row["draft_value"] == "Missing"]
        return {
            "report_type": "cycle_count_draft",
            "workflow_type": "draft",
            "workflow_name": "Cycle Count",
            "title": "Cycle Count Draft",
            "columns": ["Field", "Draft Value", "Required", "Where To Check", "Note"],
            "row_keys": ["field", "draft_value", "required", "where_to_check", "note"],
            "rows": rows,
            "total_rows": len(rows),
            "insights": [
                "This is a read-only copilot draft; it has not created a cycle count session in the database.",
                "Open the cycle count form, create the session, then add count lines for the selected products.",
                f"Missing required fields: {', '.join(missing)}." if missing else "All core required cycle count draft fields are present.",
                "After counting, submit the session, review variances, and reconcile only after verification.",
            ],
            "action_url": "/cycle-counts/new",
            "query_summary": f"Draft cycle count for {warehouse or 'selected warehouse'}",
        }

    def _workflow_answer(self, workflow_data: dict[str, Any]) -> str:
        if workflow_data.get("report_type") in {
            "purchase_order_draft",
            "sales_order_draft",
            "sales_return_draft",
            "cycle_count_draft",
        }:
            return (
                f"I prepared a {workflow_data.get('workflow_name', 'workflow')} draft from your details. "
                "Because the copilot is read-only, it has not saved anything yet. "
                "Review the table below, then open the linked form to create it manually."
            )
        workflow_name = workflow_data.get("workflow_name", "Workflow")
        return f"I drafted the standard {workflow_name} workflow. Review the step-by-step table below."

    def _workflow_action(self, workflow_data: dict[str, Any]) -> dict[str, str]:
        report_type = workflow_data.get("report_type")
        actions = {
            "purchase_order_draft": {"label": "Open purchase order form", "to": "/purchases/new"},
            "sales_order_draft": {"label": "Open sales order form", "to": "/sales/new"},
            "sales_return_draft": {"label": "Open return form", "to": "/returns/new"},
            "cycle_count_draft": {"label": "Open cycle count form", "to": "/cycle-counts/new"},
        }
        return actions.get(report_type, {"label": "Open My Tasks", "to": "/my-tasks"})

    def _is_off_topic_question(self, question: str) -> bool:
        if self._detect_report_intent(question) or self._detect_workflow_intent(question):
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

    def _parse_query_params(self, question: str, tenant_id: int) -> QueryParams:
        import re

        q = question.lower()
        params = QueryParams()

        top_match = re.search(r"\b(?:top|first|show me|give me|list)\s+(\d+)\b", q)
        bottom_match = re.search(r"\b(?:bottom|lowest|last)\s+(\d+)\b", q)
        num_match = re.search(r"\b(\d+)\s+(?:items?|products?|orders?|results?|records?)\b", q)
        if top_match:
            params.limit = int(top_match.group(1))
            params.sort_dir = "desc"
        elif bottom_match:
            params.limit = int(bottom_match.group(1))
            params.sort_dir = "asc"
        elif num_match:
            params.limit = int(num_match.group(1))

        if any(word in q for word in ["highest", "most", "largest", "biggest", "worst", "critical"]):
            params.sort_dir = "desc"
        if any(word in q for word in ["lowest", "least", "smallest", "best"]):
            params.sort_dir = "asc"

        if any(word in q for word in ["shortage", "deficit", "short"]):
            params.sort_by = "shortage"
        elif any(word in q for word in ["value", "worth"]):
            params.sort_by = "total_value"
        elif any(word in q for word in ["available", "availability"]):
            params.sort_by = "available"
        elif any(word in q for word in ["on hand", "onhand", "quantity"]):
            params.sort_by = "on_hand"

        warehouses = self.reports_repository.warehouses(tenant_id)
        for warehouse in warehouses:
            if warehouse.name.lower() in q:
                params.warehouse_id = warehouse.id
                params.warehouse_name = warehouse.name
                break

        products = self.reports_repository.products(tenant_id)
        for product in products:
            if product.name.lower() in q or (product.sku and product.sku.lower() in q):
                params.product_id = product.id
                params.product_name = product.name
                break

        categories = self.reports_repository.categories(tenant_id)
        for category in categories:
            if category.name.lower() in q:
                params.category_id = category.id
                params.category_name = category.name
                break

        today = date.today()
        if "today" in q:
            params.date_from = today
            params.date_to = today
        elif "this week" in q or "last 7 days" in q:
            params.date_from = today - timedelta(days=7)
            params.date_to = today
        elif "this month" in q or "last 30 days" in q:
            params.date_from = today - timedelta(days=30)
            params.date_to = today
        elif "last 90 days" in q or "this quarter" in q:
            params.date_from = today - timedelta(days=90)
            params.date_to = today

        threshold_match = re.search(r"\b(?:below|under|less than|fewer than)\s+(\d+)\s*(?:units?|pieces?)?\b", q)
        if threshold_match:
            params.max_available = float(threshold_match.group(1))
        above_match = re.search(r"\b(?:above|over|more than|greater than)\s+(\d+)\s*(?:units?|pieces?)?\b", q)
        if above_match:
            params.min_available = float(above_match.group(1))

        if any(word in q for word in ["low stock", "below reorder", "needs reorder", "reorder needed"]):
            params.low_stock_only = True
        if "inbound" in q or "received" in q or "stock in" in q:
            params.movement_type = "inbound"
        elif "outbound" in q or "shipped" in q or "stock out" in q:
            params.movement_type = "outbound"

        for status in [
            "DRAFT",
            "CONFIRMED",
            "FULFILLED",
            "CANCELLED",
            "SUBMITTED",
            "OPEN",
            "IN_PROGRESS",
            "COMPLETED",
            "PARTIALLY_FULFILLED",
            "RECEIVED",
        ]:
            if status.lower() in q:
                params.status_filter = status
                break
        return params

    def _fetch_report_data(self, tenant_id: int, report_type: str, params: QueryParams) -> dict[str, Any] | None:
        try:
            if report_type == "warehouse_stock":
                return self._report_warehouse_stock(tenant_id, params)
            if report_type == "low_stock":
                return self._report_low_stock(tenant_id, params)
            if report_type == "reorder_suggestions":
                return self._report_reorder(tenant_id, params)
            if report_type == "stock_movement":
                return self._report_stock_movement(tenant_id, params)
            if report_type == "blocked_stock":
                return self._report_blocked_stock(tenant_id, params)
            if report_type == "batch_expiry":
                return self._report_batch_expiry(tenant_id, params)
            if report_type == "reconciliation":
                return self._report_reconciliation(tenant_id, params)
            if report_type == "open_sales_orders":
                return self._report_open_sales_orders(tenant_id, params)
            if report_type == "pending_receipts":
                return self._report_pending_receipts(tenant_id, params)
            if report_type == "open_tasks":
                return self._report_open_tasks(tenant_id, params)
            if report_type == "inventory_summary":
                return self._report_inventory_summary(tenant_id, params)
            if report_type == "product_valuation":
                return self._report_product_valuation(tenant_id, params)
        except Exception:
            return None
        return None

    def _apply_query_params(
        self,
        rows: list[dict[str, Any]],
        params: QueryParams,
        *,
        default_sort: str | None = None,
        default_limit: int = 25,
    ) -> tuple[list[dict[str, Any]], int]:
        filtered = rows
        if params.warehouse_id:
            filtered = [row for row in filtered if row.get("warehouse_id") == params.warehouse_id]
        if params.product_id:
            filtered = [row for row in filtered if row.get("product_id") == params.product_id]
        if params.category_id:
            filtered = [row for row in filtered if row.get("category_id") == params.category_id]
        if params.category_name:
            filtered = [
                row for row in filtered
                if params.category_name.lower() in str(row.get("category") or row.get("product") or "").lower()
            ]
        if params.max_available is not None:
            filtered = [row for row in filtered if float(row.get("available", 0) or 0) <= params.max_available]
        if params.min_available is not None:
            filtered = [row for row in filtered if float(row.get("available", 0) or 0) >= params.min_available]
        if params.status_filter:
            filtered = [row for row in filtered if str(row.get("status", "")).upper() == params.status_filter]
        if params.movement_type == "inbound":
            filtered = [row for row in filtered if float(row.get("delta", 0) or 0) > 0]
        elif params.movement_type == "outbound":
            filtered = [row for row in filtered if float(row.get("delta", 0) or 0) < 0]

        sort_key = params.sort_by or default_sort
        if sort_key:
            filtered.sort(key=lambda row: row.get(sort_key, 0) or 0, reverse=params.sort_dir == "desc")
        total_rows = len(filtered)
        return filtered[: params.limit or default_limit], total_rows

    def _query_summary(self, params: QueryParams) -> str | None:
        parts = []
        if params.limit:
            parts.append(f"Top {params.limit}")
        if params.sort_by:
            sort_text = f"by {params.sort_by.replace('_', ' ')}"
            if params.sort_dir == "asc":
                sort_text = f"lowest {sort_text}"
            parts.append(sort_text)
        if params.warehouse_name:
            parts.append(f"in {params.warehouse_name}")
        if params.product_name:
            parts.append(f"product: {params.product_name}")
        if params.category_name:
            parts.append(f"category: {params.category_name}")
        if params.max_available is not None:
            parts.append(f"available < {params.max_available:g}")
        if params.min_available is not None:
            parts.append(f"available > {params.min_available:g}")
        if params.movement_type:
            parts.append(f"{params.movement_type} only")
        if params.status_filter:
            parts.append(f"status: {params.status_filter}")
        return " · ".join(parts) if parts else None

    def _insights_with_context(
        self,
        *,
        report_type: str,
        rows: list[dict[str, Any]],
        params: QueryParams,
        total: int,
    ) -> list[str]:
        insights = []
        if params.limit and total > params.limit:
            insights.append(f"Showing {params.limit} of {total} results matching your query.")
        if params.warehouse_name:
            insights.append(f"Filtered to {params.warehouse_name} only.")
        if report_type == "low_stock":
            zero = [row for row in rows if row.get("available", 1) <= 0]
            if zero:
                insights.append(f"{len(zero)} of these have zero available stock - urgent action required.")
            if rows:
                worst = rows[0]
                insights.append(
                    f"Most critical: {worst['product']} with {worst['available']} units available "
                    f"(reorder level: {worst.get('reorder_level', '?')})."
                )
        elif report_type == "warehouse_stock":
            total_available = sum(float(row.get("available", 0) or 0) for row in rows)
            insights.append(f"Total available across shown items: {round(total_available, 2)} units.")
        elif report_type == "stock_movement":
            inbound = sum(float(row.get("delta", 0) or 0) for row in rows if float(row.get("delta", 0) or 0) > 0)
            outbound = sum(float(row.get("delta", 0) or 0) for row in rows if float(row.get("delta", 0) or 0) < 0)
            insights.append(f"Shown movements net to {round(inbound + outbound, 2)} units.")
        return insights

    def _report_warehouse_stock(self, tenant_id: int, params: QueryParams) -> dict[str, Any]:
        stock_rows = self.reports_repository.stock(tenant_id)
        products = {p.id: p for p in self.reports_repository.products(tenant_id)}
        warehouses = {w.id: w for w in self.reports_repository.warehouses(tenant_id)}
        categories = {c.id: c for c in self.reports_repository.categories(tenant_id)}
        rows = []
        for stock in stock_rows:
            product = products.get(stock.product_id)
            warehouse = warehouses.get(stock.warehouse_id)
            category = categories.get(product.category_id) if product and product.category_id else None
            available = float(stock.quantity_available or 0)
            if params.low_stock_only and product and float(product.reorder_level or 0) > 0:
                if available >= float(product.reorder_level or 0):
                    continue
            rows.append(
                {
                    "product_id": stock.product_id,
                    "warehouse_id": stock.warehouse_id,
                    "category_id": product.category_id if product else None,
                    "product": product.name if product else f"#{stock.product_id}",
                    "sku": product.sku if product else "",
                    "warehouse": warehouse.name if warehouse else f"#{stock.warehouse_id}",
                    "category": category.name if category else "",
                    "on_hand": round(float(stock.quantity_on_hand or 0), 2),
                    "reserved": round(float(stock.quantity_reserved or 0), 2),
                    "available": round(available, 2),
                    "reorder_level": float(product.reorder_level or 0) if product else 0,
                }
            )
        rows, total_rows = self._apply_query_params(rows, params, default_sort=params.sort_by or "available")
        title = "Warehouse Stock"
        if params.warehouse_name:
            title = f"{title} - {params.warehouse_name}"
        insights = self._insights_warehouse_stock(rows) + self._insights_with_context(
            report_type="warehouse_stock",
            rows=rows,
            params=params,
            total=total_rows,
        )
        return {
            "report_type": "warehouse_stock",
            "title": title,
            "columns": ["Product", "SKU", "Warehouse", "On Hand", "Reserved", "Available", "Reorder Level"],
            "row_keys": ["product", "sku", "warehouse", "on_hand", "reserved", "available", "reorder_level"],
            "rows": rows,
            "total_rows": total_rows,
            "insights": insights,
            "action_url": "/reports/warehouse-stock",
            "query_summary": self._query_summary(params),
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

    def _report_low_stock(self, tenant_id: int, params: QueryParams) -> dict[str, Any]:
        stock_rows = self.reports_repository.stock(tenant_id)
        products = {p.id: p for p in self.reports_repository.products(tenant_id)}
        warehouses = {w.id: w for w in self.reports_repository.warehouses(tenant_id)}
        rows = []
        for stock in stock_rows:
            product = products.get(stock.product_id)
            if not product or not product.reorder_level or float(product.reorder_level) <= 0:
                continue
            available = float(stock.quantity_available or 0)
            if available < float(product.reorder_level):
                warehouse = warehouses.get(stock.warehouse_id)
                rows.append(
                    {
                        "product_id": stock.product_id,
                        "warehouse_id": stock.warehouse_id,
                        "category_id": product.category_id,
                        "product": product.name,
                        "sku": product.sku or "",
                        "warehouse": warehouse.name if warehouse else f"#{stock.warehouse_id}",
                        "available": round(available, 2),
                        "reorder_level": float(product.reorder_level),
                        "shortage": round(float(product.reorder_level) - available, 2),
                    }
                )
        rows, total_rows = self._apply_query_params(rows, params, default_sort=params.sort_by or "shortage")
        if not rows:
            insights = ["All products are above their reorder levels. Stock health is good."]
        else:
            critical = [row for row in rows if row["available"] <= 0]
            insights = [
                f"{total_rows} products are below reorder level.",
                f"Total shortage units across all low-stock items: {round(sum(row['shortage'] for row in rows), 2)}.",
            ]
            if critical:
                insights.insert(1, f"{len(critical)} products have zero or negative available stock - urgent action required.")
        insights.extend(self._insights_with_context(report_type="low_stock", rows=rows, params=params, total=total_rows))
        return {
            "report_type": "low_stock",
            "title": "Low Stock Report",
            "columns": ["Product", "SKU", "Warehouse", "Available", "Reorder Level", "Shortage"],
            "row_keys": ["product", "sku", "warehouse", "available", "reorder_level", "shortage"],
            "rows": rows,
            "total_rows": total_rows,
            "insights": insights,
            "action_url": "/reports/low-stock",
            "query_summary": self._query_summary(params),
        }

    def _report_reorder(self, tenant_id: int, params: QueryParams) -> dict[str, Any]:
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
                        "product_id": stock.product_id,
                        "warehouse_id": stock.warehouse_id,
                        "category_id": product.category_id,
                        "product": product.name,
                        "sku": product.sku or "",
                        "available": round(available, 2),
                        "reorder_level": float(product.reorder_level),
                        "suggested_qty": round(float(product.reorder_level) * 2 - available, 2),
                    }
                )
        rows, total_rows = self._apply_query_params(rows, params, default_sort=params.sort_by or "suggested_qty")
        return {
            "report_type": "reorder_suggestions",
            "title": "Reorder Suggestions",
            "columns": ["Product", "SKU", "Available", "Reorder Level", "Suggested Order Qty"],
            "row_keys": ["product", "sku", "available", "reorder_level", "suggested_qty"],
            "rows": rows,
            "total_rows": total_rows,
            "insights": [
                f"{total_rows} products need reordering.",
                "Suggested quantities are 2x the reorder level minus current available stock.",
            ] if rows else ["No products currently need reordering."],
            "action_url": "/purchases/new",
            "query_summary": self._query_summary(params),
        }

    def _report_stock_movement(self, tenant_id: int, params: QueryParams) -> dict[str, Any]:
        date_from = params.date_from or date.today() - timedelta(days=7)
        date_to = params.date_to or date.today()
        entries = self.reports_repository.ledger(tenant_id, date_from=date_from, date_to=date_to)
        products = {p.id: p for p in self.reports_repository.products(tenant_id)}
        warehouses = {w.id: w for w in self.reports_repository.warehouses(tenant_id)}
        rows = []
        for entry in list(reversed(entries))[-50:]:
            product = products.get(entry.product_id)
            warehouse = warehouses.get(entry.warehouse_id)
            rows.append(
                {
                    "product_id": entry.product_id,
                    "warehouse_id": entry.warehouse_id,
                    "category_id": product.category_id if product else None,
                    "date": entry.created_at.strftime("%Y-%m-%d") if entry.created_at else "",
                    "product": product.name if product else f"#{entry.product_id}",
                    "warehouse": warehouse.name if warehouse else f"#{entry.warehouse_id}",
                    "movement_type": self._enum_value(entry.movement_type),
                    "delta": round(float(entry.quantity_delta or 0), 2),
                    "reference": self._enum_value(entry.reference_type),
                }
            )
        rows, total_rows = self._apply_query_params(rows, params, default_sort=params.sort_by)
        inbound = sum(row["delta"] for row in rows if row["delta"] > 0)
        outbound = sum(row["delta"] for row in rows if row["delta"] < 0)
        return {
            "report_type": "stock_movement",
            "title": f"Stock Movements ({date_from} to {date_to})",
            "columns": ["Date", "Product", "Warehouse", "Type", "Delta", "Reference"],
            "row_keys": ["date", "product", "warehouse", "movement_type", "delta", "reference"],
            "rows": rows,
            "total_rows": total_rows,
            "insights": [
                f"{total_rows} movements in the selected period.",
                f"Total inbound: +{round(inbound, 2)} units.",
                f"Total outbound: {round(outbound, 2)} units (net: {round(inbound + outbound, 2)}).",
            ] + self._insights_with_context(report_type="stock_movement", rows=rows, params=params, total=total_rows),
            "action_url": "/reports/stock-movements",
            "query_summary": self._query_summary(params),
        }

    def _report_blocked_stock(self, tenant_id: int, params: QueryParams) -> dict[str, Any]:
        blocked = self.reports_repository.blocked_return_stock(tenant_id)
        products = {p.id: p for p in self.reports_repository.products(tenant_id)}
        rows = []
        for row in blocked:
            product = products.get(row.product_id)
            rows.append(
                {
                    "product_id": row.product_id,
                    "warehouse_id": row.warehouse_id,
                    "category_id": product.category_id if product else None,
                    "product": product.name if product else f"#{row.product_id}",
                    "sku": product.sku if product else "",
                    "quantity": round(float(row.quantity or 0), 2),
                    "reason": row.reason or self._enum_value(row.status),
                }
            )
        rows, total_rows = self._apply_query_params(rows, params, default_sort=params.sort_by or "quantity")
        return {
            "report_type": "blocked_stock",
            "title": "Blocked Stock Report",
            "columns": ["Product", "SKU", "Quantity", "Reason"],
            "row_keys": ["product", "sku", "quantity", "reason"],
            "rows": rows,
            "total_rows": total_rows,
            "insights": [
                f"{total_rows} blocked stock records.",
                f"Total blocked units: {round(sum(row['quantity'] for row in rows), 2)}.",
            ] if rows else ["No blocked stock found."],
            "action_url": "/reports/blocked-stock",
            "query_summary": self._query_summary(params),
        }

    def _report_open_sales_orders(self, tenant_id: int, params: QueryParams) -> dict[str, Any]:
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
                    "customer_id": order.customer_id,
                    "order_number": order.order_number,
                    "customer": customer.name if customer else f"#{order.customer_id}",
                    "status": status,
                    "created_at": order.created_at.strftime("%Y-%m-%d") if order.created_at else "",
                }
            )
        rows, total_rows = self._apply_query_params(rows, params, default_sort=None)
        by_status: dict[str, int] = {}
        for row in rows:
            by_status[row["status"]] = by_status.get(row["status"], 0) + 1
        insights = [f"{total_rows} open sales orders."]
        for status, count in sorted(by_status.items()):
            insights.append(f"{count} in {status}.")
        return {
            "report_type": "open_sales_orders",
            "title": "Open Sales Orders",
            "columns": ["Order Number", "Customer", "Status", "Created"],
            "row_keys": ["order_number", "customer", "status", "created_at"],
            "rows": rows,
            "total_rows": total_rows,
            "insights": insights,
            "action_url": "/sales",
            "query_summary": self._query_summary(params),
        }

    def _report_pending_receipts(self, tenant_id: int, params: QueryParams) -> dict[str, Any]:
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
        rows, total_rows = self._apply_query_params(rows, params, default_sort=None)
        return {
            "report_type": "pending_receipts",
            "title": "Pending Purchase Receipts",
            "columns": ["Receipt ID", "PO ID", "Status", "Created"],
            "row_keys": ["receipt_id", "po_id", "status", "created_at"],
            "rows": rows,
            "total_rows": total_rows,
            "insights": [f"{total_rows} pending receipts awaiting commitment."] if rows else ["No pending receipts."],
            "action_url": "/purchase-receipts",
            "query_summary": self._query_summary(params),
        }

    def _report_open_tasks(self, tenant_id: int, params: QueryParams) -> dict[str, Any]:
        tasks = self.workflow_repository.get_all_tasks(tenant_id, WorkflowTaskStatus.OPEN.value)
        by_role: dict[str, int] = {}
        rows = []
        for task in tasks:
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
        rows, total_rows = self._apply_query_params(rows, params, default_sort=None)
        insights = [f"{total_rows} open workflow tasks total."]
        for role, count in sorted(by_role.items(), key=lambda item: -item[1]):
            insights.append(f"{count} tasks for {role.replace('_', ' ').title()}.")
        return {
            "report_type": "open_tasks",
            "title": "Open Workflow Tasks",
            "columns": ["Title", "Assigned Role", "Step", "Priority", "Created"],
            "row_keys": ["title", "role", "step", "priority", "created_at"],
            "rows": rows,
            "total_rows": total_rows,
            "insights": insights,
            "action_url": "/my-tasks",
            "query_summary": self._query_summary(params),
        }

    def _report_inventory_summary(self, tenant_id: int, params: QueryParams) -> dict[str, Any]:
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
            "query_summary": self._query_summary(params),
        }

    def _report_batch_expiry(self, tenant_id: int, params: QueryParams) -> dict[str, Any]:
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
                    "product_id": batch.product_id,
                    "warehouse_id": batch.warehouse_id,
                    "category_id": product.category_id if product else None,
                    "product": product.name if product else f"#{batch.product_id}",
                    "batch": batch.batch_number or f"#{batch.id}",
                    "expiry_date": expiry.isoformat(),
                    "quantity": round(float(batch.quantity_on_hand or 0), 2),
                    "status": "EXPIRED" if expiry < today else "EXPIRING SOON",
                }
            )
        rows, total_rows = self._apply_query_params(rows, params, default_sort=params.sort_by or "expiry_date")
        expired = [row for row in rows if row["status"] == "EXPIRED"]
        expiring = [row for row in rows if row["status"] == "EXPIRING SOON"]
        return {
            "report_type": "batch_expiry",
            "title": "Batch Expiry Report (Next 30 Days + Already Expired)",
            "columns": ["Product", "Batch", "Expiry Date", "Quantity", "Status"],
            "row_keys": ["product", "batch", "expiry_date", "quantity", "status"],
            "rows": rows,
            "total_rows": total_rows,
            "insights": [
                f"{len(expired)} batches already expired." if expired else "No expired batches.",
                f"{len(expiring)} batches expiring within 30 days." if expiring else "No batches expiring soon.",
            ],
            "action_url": "/reports/batch-expiry",
            "query_summary": self._query_summary(params),
        }

    def _report_reconciliation(self, tenant_id: int, params: QueryParams) -> dict[str, Any]:
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
                        "product_id": stock.product_id,
                        "warehouse_id": stock.warehouse_id,
                        "category_id": product.category_id if product else None,
                        "product": product.name if product else f"#{stock.product_id}",
                        "ledger_qty": ledger_qty,
                        "projection_qty": projection_qty,
                        "variance": variance,
                    }
                )
        rows, total_rows = self._apply_query_params(rows, params, default_sort=params.sort_by or "variance")
        return {
            "report_type": "reconciliation",
            "title": "Reconciliation Report",
            "columns": ["Product", "Ledger Qty", "Projection Qty", "Variance"],
            "row_keys": ["product", "ledger_qty", "projection_qty", "variance"],
            "rows": rows,
            "total_rows": total_rows,
            "insights": [
                f"{total_rows} mismatches found between ledger and projection.",
                "Run the reconciliation process to correct projections." if rows else "",
                "All stock projections are in sync with the ledger." if not rows else "",
            ],
            "action_url": "/reports/reconciliation",
            "query_summary": self._query_summary(params),
        }

    def _report_product_valuation(self, tenant_id: int, params: QueryParams) -> dict[str, Any]:
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
                        "product_id": stock.product_id,
                        "warehouse_id": stock.warehouse_id,
                        "category_id": product.category_id,
                        "product": product.name,
                        "sku": product.sku or "",
                        "quantity": round(quantity, 2),
                        "cost_price": round(cost, 2),
                        "total_value": total_value,
                    }
                )
        rows, total_rows = self._apply_query_params(rows, params, default_sort=params.sort_by or "total_value")
        total_value = round(sum(row["total_value"] for row in rows), 2)
        return {
            "report_type": "product_valuation",
            "title": "Product Valuation Report",
            "columns": ["Product", "SKU", "Quantity", "Cost Price", "Total Value"],
            "row_keys": ["product", "sku", "quantity", "cost_price", "total_value"],
            "rows": rows,
            "total_rows": total_rows,
            "insights": [
                f"Total inventory value: {total_value}.",
                f"Top product by value: {rows[0]['product']} ({rows[0]['total_value']})." if rows else "",
            ],
            "action_url": "/reports/product-valuation",
            "query_summary": self._query_summary(params),
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
        history: list[dict] | None = None,
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
                {"role": msg["role"], "content": msg["content"]}
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
