from datetime import date, timedelta, timezone
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.assistant import AssistantFeedbackValue, AssistantMessageRole, FAQChunk, FAQDocument, KnowledgeSourceType
from app.models.audit import AuditLog
from app.models.auth import Tenant, TenantStatus, User, UserRole, UserStatus
from app.models.inventory import WarehouseStock
from app.models.master_data import Product, RecordStatus, Warehouse, WarehouseLocation
from app.services.assistant import AssistantService


class _FakeAssistantMongoRepository:
    def __init__(self) -> None:
        self.next_id = 1
        self.sessions: dict[int, dict] = {}
        self.messages: dict[int, dict] = {}
        self.feedback: dict[int, dict] = {}

    def _id(self) -> int:
        value = self.next_id
        self.next_id += 1
        return value

    def _now(self):
        from datetime import datetime

        return datetime.now(timezone.utc)

    def create_session(self, *, tenant_id: int, user_id: int, title: str) -> dict:
        session_id = self._id()
        session = {
            "id": session_id,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "title": title,
            "metadata_json": None,
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.sessions[session_id] = session
        return session

    def get_session(self, *, tenant_id: int, session_id: int) -> dict | None:
        session = self.sessions.get(session_id)
        if not session or session["tenant_id"] != tenant_id:
            return None
        return session

    def update_session_title(self, session_id: int, title: str) -> None:
        if session_id in self.sessions:
            self.sessions[session_id]["title"] = title

    def update_session_timestamp(self, session_id: int) -> None:
        if session_id in self.sessions:
            self.sessions[session_id]["updated_at"] = self._now()

    def list_sessions_for_user(self, *, tenant_id: int, user_id: int) -> list[dict]:
        return [
            session for session in self.sessions.values()
            if session["tenant_id"] == tenant_id and session["user_id"] == user_id
        ]

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
        message_id = self._id()
        message = {
            "id": message_id,
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
            "created_at": self._now(),
        }
        self.messages[message_id] = message
        return message

    def list_messages(self, *, tenant_id: int, session_id: int) -> list[dict]:
        return [
            message for message in self.messages.values()
            if message["tenant_id"] == tenant_id and message["session_id"] == session_id
        ]

    def count_messages(self, *, tenant_id: int, session_id: int) -> int:
        return len(self.list_messages(tenant_id=tenant_id, session_id=session_id))

    def get_message(self, *, tenant_id: int, message_id: int) -> dict | None:
        message = self.messages.get(message_id)
        if not message or message["tenant_id"] != tenant_id:
            return None
        return message

    def upsert_feedback(
        self,
        *,
        tenant_id: int,
        message_id: int,
        user_id: int,
        value: str,
        note: str | None,
    ) -> dict:
        feedback = {
            "id": self._id(),
            "tenant_id": tenant_id,
            "message_id": message_id,
            "user_id": user_id,
            "value": value,
            "note": note,
            "created_at": self._now(),
        }
        self.feedback[message_id] = feedback
        return feedback

    def get_telemetry(self, *, tenant_id: int) -> dict:
        assistant_messages = [
            message for message in self.messages.values()
            if message["tenant_id"] == tenant_id and message["role"] == AssistantMessageRole.ASSISTANT.value
        ]
        total_tokens = sum(int((message.get("usage_json") or {}).get("total_tokens", 0)) for message in assistant_messages)
        return {
            "total_requests": len(assistant_messages),
            "avg_latency_ms": 0.0,
            "total_tokens": total_tokens,
            "abstain_rate_pct": 0.0,
            "citation_rate_pct": 100.0 if assistant_messages else 0.0,
        }


def _assistant_service(db: Session) -> AssistantService:
    service = AssistantService(db)
    service.mongo_repo = _FakeAssistantMongoRepository()
    return service


def _create_tenant(db: Session, *, company: str, email: str) -> Tenant:
    tenant = Tenant(company_name=company, contact_email=email, status=TenantStatus.ACTIVE)
    db.add(tenant)
    db.flush()
    return tenant


def _create_user(
    db: Session,
    *,
    tenant_id: int,
    email: str,
    role: UserRole,
    password: str = "StrongPass123!",
) -> User:
    user = User(
        tenant_id=tenant_id,
        name=email.split("@")[0],
        email=email,
        password_hash=get_password_hash(password),
        role=role,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    db.flush()
    return user


def _register_and_login(client: TestClient, email: str = "assistant-admin@example.com") -> tuple[str, int]:
    register = client.post(
        "/api/auth/register",
        json={
            "company_name": "Assistant Co",
            "name": "Assistant Admin",
            "email": email,
            "password": "StrongPass123!",
        },
    )
    assert register.status_code == 201
    login = client.post("/api/auth/login", json={"email": email, "password": "StrongPass123!"})
    assert login.status_code == 200
    payload = login.json()
    return payload["access_token"], payload["user"]["tenant_id"]


def _create_doc_chunk(
    db: Session,
    *,
    tenant_id: int | None,
    slug: str,
    text: str,
) -> FAQChunk:
    doc = FAQDocument(
        tenant_id=tenant_id,
        slug=slug,
        title=f"Doc {slug}",
        source_type=KnowledgeSourceType.DOC,
        source_uri=f"docs/{slug}.md",
        body_text=text,
        metadata_json={"source_uri": f"docs/{slug}.md", "action_to": "/reports"},
        checksum=f"checksum-{slug}",
    )
    db.add(doc)
    db.flush()
    chunk = FAQChunk(
        tenant_id=tenant_id,
        document_id=doc.id,
        chunk_index=0,
        content=text,
        searchable_text=text.lower(),
        embedding=None,
        token_count=len(text.split()),
        metadata_json={
            "title": doc.title,
            "source_type": doc.source_type.value,
            "source_uri": doc.source_uri,
            "action_to": "/reports",
        },
    )
    db.add(chunk)
    db.flush()
    return chunk


def test_keyword_search_tokenizes_question_terms(db_session: Session):
    tenant = _create_tenant(db_session, company="Search Co", email="search@example.com")
    _create_doc_chunk(
        db_session,
        tenant_id=None,
        slug="reconciliation-help",
        text="Reconciliation reports show mismatch rows when ledger balances do not match expected stock.",
    )
    db_session.commit()

    rows = AssistantService(db_session).repository.search_keyword_chunks(
        tenant_id=tenant.id,
        term="How do I fix a reconciliation mismatch?",
        limit=5,
    )

    assert rows
    joined = " ".join(row.searchable_text for row in rows)
    assert "reconciliation" in joined or "mismatch" in joined


def test_parse_query_params_extracts_top_low_stock(db_session: Session):
    params = _assistant_service(db_session)._parse_query_params(
        "show me top 5 low stock products",
        tenant_id=1,
    )

    assert params.limit == 5
    assert params.low_stock_only is True
    assert params.sort_dir == "desc"


def test_parse_query_params_extracts_limit_and_threshold(db_session: Session):
    params = _assistant_service(db_session)._parse_query_params(
        "give me 3 items below 10 units",
        tenant_id=1,
    )

    assert params.limit == 3
    assert params.max_available == 10.0


def test_parse_query_params_extracts_week_range(db_session: Session):
    params = _assistant_service(db_session)._parse_query_params(
        "show stock movements this week",
        tenant_id=1,
    )

    assert params.date_from == date.today() - timedelta(days=7)
    assert params.date_to == date.today()


def test_lexical_score_rewards_relevant_terms(db_session: Session):
    score = AssistantService(db_session)._lexical_score(
        "reconciliation mismatch",
        "reconciliation reports show mismatches between ledger",
    )

    assert score > 0.3


def test_chunk_text_uses_smaller_overlapping_chunks(db_session: Session):
    text = "A" * 2000
    chunks = AssistantService(db_session)._chunk_text(
        text,
        source_uri="docs/test.md",
        title="Long Test",
        source_type=KnowledgeSourceType.DOC.value,
        action_to="/reports",
    )

    assert len(chunks) > 1
    assert all(len(chunk["content"]) < 700 for chunk in chunks)


def test_reindex_global_knowledge_indexes_operational_sources(db_session: Session, monkeypatch):
    service = AssistantService(db_session)
    monkeypatch.setattr(service, "_embed_many", lambda texts: [None for _ in texts])

    result = service.reindex_global_knowledge()

    assert result["documents_indexed"] >= 8
    assert result["chunks_indexed"] >= result["documents_indexed"]


def test_detect_report_intent_for_warehouse_stock(db_session: Session):
    intent = AssistantService(db_session)._detect_report_intent("show me warehouse stock report")

    assert intent is not None
    assert intent["report_type"] == "warehouse_stock"


def test_detect_report_intent_ignores_off_topic_question(db_session: Session):
    intent = AssistantService(db_session)._detect_report_intent("what is the weather today")

    assert intent is None


def test_tenant_admin_can_create_assistant_session(client: TestClient):
    token, _ = _register_and_login(client)
    response = client.post(
        "/api/assistant/sessions",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Ops Review"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Ops Review"
    assert body["id"] > 0


def test_non_admin_cannot_access_copilot(client: TestClient, db_session: Session):
    _, tenant_id = _register_and_login(client, "assistant-rbac-admin@example.com")
    user = _create_user(
        db_session,
        tenant_id=tenant_id,
        email="assistant-im@example.com",
        role=UserRole.INVENTORY_MANAGER,
    )
    db_session.commit()
    login = client.post("/api/auth/login", json={"email": user.email, "password": "StrongPass123!"})
    assert login.status_code == 200
    token = login.json()["access_token"]

    response = client.post(
        "/api/assistant/sessions",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Should fail"},
    )
    assert response.status_code == 403


def test_retrieval_is_tenant_isolated(db_session: Session):
    tenant_a = _create_tenant(db_session, company="Tenant A", email="a@example.com")
    tenant_b = _create_tenant(db_session, company="Tenant B", email="b@example.com")
    _create_doc_chunk(db_session, tenant_id=None, slug="global-workflow", text="workflow queue delay and pick tasks")
    _create_doc_chunk(db_session, tenant_id=tenant_a.id, slug="tenant-a-doc", text="workflow queue delay and cycle count")
    _create_doc_chunk(db_session, tenant_id=tenant_b.id, slug="tenant-b-secret", text="workflow queue delay and hidden details")
    db_session.commit()

    service = AssistantService(db_session)
    rows = service._retrieve_chunks(tenant_id=tenant_a.id, question="workflow queue delay")

    assert rows
    tenant_ids = {row["chunk"].tenant_id for row in rows}
    assert tenant_b.id not in tenant_ids
    assert tenant_ids.issubset({None, tenant_a.id})


def test_confidence_policy_abstains_without_citations(db_session: Session):
    service = AssistantService(db_session)
    result = service._apply_confidence_policy(
        {"answer": "Confident answer", "confidence": "HIGH", "confidence_score": 0.99},
        [],
    )
    assert result["abstained"] is True
    assert result["confidence"] == "LOW"
    assert "don’t know" in result["answer"].lower()


def test_confidence_policy_abstains_on_low_score(db_session: Session):
    chunk = SimpleNamespace(
        id=42,
        content="Relevant text",
        metadata_json={"title": "Doc", "source_type": "DOC", "source_uri": "docs/test.md", "action_to": "/reports"},
    )
    service = AssistantService(db_session)
    result = service._apply_confidence_policy(
        {"answer": "Maybe", "confidence": "MEDIUM", "confidence_score": 0.15},
        [{"chunk": chunk, "score": 0.31}],
    )
    assert result["abstained"] is True
    assert result["confidence"] == "LOW"
    assert len(result["citations"]) == 1


def test_session_message_feedback_lifecycle_with_audit(db_session: Session, monkeypatch):
    tenant = _create_tenant(db_session, company="Lifecycle Co", email="life@example.com")
    admin = _create_user(
        db_session,
        tenant_id=tenant.id,
        email="tenant-admin@example.com",
        role=UserRole.TENANT_ADMIN,
    )
    chunk = _create_doc_chunk(
        db_session,
        tenant_id=None,
        slug="ops-source",
        text="open tasks should be prioritized by role and queue size",
    )
    db_session.commit()

    service = _assistant_service(db_session)
    session = service.create_session(tenant_id=tenant.id, user_id=admin.id, title="Daily Ops")

    monkeypatch.setattr(
        service,
        "_retrieve_chunks",
        lambda tenant_id, question: [{"chunk": chunk, "score": 0.92}],
    )
    monkeypatch.setattr(
        service,
        "_grounded_answer",
        lambda **kwargs: (
            {
                "answer": "Prioritize OPEN tasks for the largest role queue first.",
                "confidence": "HIGH",
                "confidence_score": 0.88,
                "suggested_actions": [{"label": "Open My Tasks", "to": "/my-tasks"}],
            },
            {"total_tokens": 321},
        ),
    )

    ask_result = service.ask_session(
        tenant_id=tenant.id,
        user_id=admin.id,
        role=UserRole.TENANT_ADMIN,
        session_id=session["id"],
        question="What should I do first today?",
    )
    assert ask_result["message"]["role"] == AssistantMessageRole.ASSISTANT.value
    assert ask_result["confidence"] == "HIGH"
    assert ask_result["citations"]
    assert ask_result["suggested_actions"]

    feedback = service.add_feedback(
        tenant_id=tenant.id,
        user_id=admin.id,
        message_id=ask_result["message"]["id"],
        value=AssistantFeedbackValue.UP.value,
        note="Useful and grounded",
    )
    assert feedback["value"] == AssistantFeedbackValue.UP.value

    detail = service.get_session_detail(tenant_id=tenant.id, user_id=admin.id, session_id=session["id"])
    assert len(detail["messages"]) == 2
    assert detail["messages"][-1]["content"].startswith("Prioritize OPEN tasks")

    telemetry = service.telemetry(tenant_id=tenant.id)
    assert telemetry["total_requests"] >= 1
    assert telemetry["total_tokens"] >= 321

    audit_actions = {
        row.action
        for row in db_session.scalars(
            select(AuditLog).where(AuditLog.tenant_id == tenant.id)
        )
    }
    assert "ASSISTANT_SESSION_CREATE" in audit_actions
    assert "ASSISTANT_COPILOT_ASK" in audit_actions
    assert "ASSISTANT_FEEDBACK" in audit_actions

    assert any(
        message["role"] == AssistantMessageRole.ASSISTANT.value
        for message in service.mongo_repo.messages.values()
    )


def test_ask_session_returns_low_stock_report_data(db_session: Session, monkeypatch):
    tenant = _create_tenant(db_session, company="Report Co", email="report@example.com")
    admin = _create_user(
        db_session,
        tenant_id=tenant.id,
        email="report-admin@example.com",
        role=UserRole.TENANT_ADMIN,
    )
    warehouse = Warehouse(
        tenant_id=tenant.id,
        name="Main Warehouse",
        code="MAIN",
        status=RecordStatus.ACTIVE,
    )
    db_session.add(warehouse)
    db_session.flush()
    location = WarehouseLocation(
        tenant_id=tenant.id,
        warehouse_id=warehouse.id,
        code="A1",
        name="Aisle 1",
        status=RecordStatus.ACTIVE,
    )
    product = Product(
        tenant_id=tenant.id,
        name="Blue Widget",
        sku="BW-001",
        unit="pcs",
        reorder_level=20,
        cost_price=5,
        status=RecordStatus.ACTIVE,
    )
    db_session.add_all([location, product])
    db_session.flush()
    db_session.add(
        WarehouseStock(
            tenant_id=tenant.id,
            product_id=product.id,
            warehouse_id=warehouse.id,
            location_id=location.id,
            quantity_on_hand=8,
            quantity_reserved=2,
            quantity_available=6,
        )
    )
    chunk = _create_doc_chunk(
        db_session,
        tenant_id=None,
        slug="low-stock-report",
        text="Low stock reports show products below reorder levels and shortage quantities.",
    )
    db_session.commit()

    service = _assistant_service(db_session)
    session = service.create_session(tenant_id=tenant.id, user_id=admin.id, title="Report Data")
    monkeypatch.setattr(
        service,
        "_retrieve_chunks",
        lambda tenant_id, question: [{"chunk": chunk, "score": 0.9}],
    )
    monkeypatch.setattr(
        service,
        "_grounded_answer",
        lambda **kwargs: (
            {
                "answer": "Here is the low stock report.",
                "confidence": "HIGH",
                "confidence_score": 0.9,
                "suggested_actions": [{"label": "Open Low Stock", "to": "/reports/low-stock"}],
                "is_off_topic": False,
            },
            {"total_tokens": 12},
        ),
    )

    result = service.ask_session(
        tenant_id=tenant.id,
        user_id=admin.id,
        role=UserRole.TENANT_ADMIN,
        session_id=session["id"],
        question="show top 5 low stock",
    )

    assert result["report_data"]["report_type"] == "low_stock"
    assert isinstance(result["report_data"]["rows"], list)
    assert len(result["report_data"]["rows"]) <= 5
    assert result["report_data"]["rows"][0]["product"] == "Blue Widget"


def test_ask_session_returns_workflow_draft(db_session: Session, monkeypatch):
    tenant = _create_tenant(db_session, company="Workflow Co", email="workflow@example.com")
    admin = _create_user(
        db_session,
        tenant_id=tenant.id,
        email="workflow-admin@example.com",
        role=UserRole.TENANT_ADMIN,
    )
    chunk = _create_doc_chunk(
        db_session,
        tenant_id=None,
        slug="sales-workflow-draft",
        text="Sales order workflow includes confirmation, picking, packing, fulfillment, and invoicing.",
    )
    db_session.commit()

    service = _assistant_service(db_session)
    session = service.create_session(tenant_id=tenant.id, user_id=admin.id, title="Workflow Draft")
    monkeypatch.setattr(
        service,
        "_retrieve_chunks",
        lambda tenant_id, question: [{"chunk": chunk, "score": 0.9}],
    )
    monkeypatch.setattr(
        service,
        "_grounded_answer",
        lambda **kwargs: (
            {
                "answer": "Here is the draft sales order workflow.",
                "confidence": "HIGH",
                "confidence_score": 0.9,
                "suggested_actions": [{"label": "Open My Tasks", "to": "/my-tasks"}],
                "is_off_topic": False,
            },
            {"total_tokens": 12},
        ),
    )

    result = service.ask_session(
        tenant_id=tenant.id,
        user_id=admin.id,
        role=UserRole.TENANT_ADMIN,
        session_id=session["id"],
        question="draft a sales order workflow",
    )

    assert result["report_data"]["workflow_type"] == "draft"
    assert result["report_data"]["workflow_name"] == "Sales Order"
    assert len(result["report_data"]["rows"]) == 6


def test_ask_session_returns_purchase_order_detail_draft(db_session: Session):
    tenant = _create_tenant(db_session, company="PO Draft Co", email="po-draft@example.com")
    admin = _create_user(
        db_session,
        tenant_id=tenant.id,
        email="po-draft-admin@example.com",
        role=UserRole.TENANT_ADMIN,
    )
    db_session.commit()

    service = _assistant_service(db_session)
    session = service.create_session(tenant_id=tenant.id, user_id=admin.id, title="PO Draft")

    result = service.ask_session(
        tenant_id=tenant.id,
        user_id=admin.id,
        role=UserRole.TENANT_ADMIN,
        session_id=session["id"],
        question=(
            "Draft a purchase order workflow for 50 units of Caffeine Body Scrub from Vendor #1. "
            "Use these field details: - Product: Caffeine Body Scrub - SKU: MCA-BC-001 "
            "- Quantity: 50 - Vendor: Vendor #1 - Warehouse: Main Warehouse "
            "- Expected delivery date: 2026-06-15 - Unit cost: 120.00 "
            "- Notes: Reorder because current available stock is below reorder level."
        ),
    )

    assert result["confidence"] == "HIGH"
    assert result["report_data"]["report_type"] == "purchase_order_draft"
    assert result["report_data"]["workflow_name"] == "Purchase Order"
    row_values = {row["field"]: row["draft_value"] for row in result["report_data"]["rows"]}
    assert row_values["Product"] == "Caffeine Body Scrub"
    assert row_values["SKU"] == "MCA-BC-001"
    assert row_values["Quantity"] == "50"
    assert row_values["Vendor"] == "Vendor #1"
    assert row_values["Warehouse"] == "Main Warehouse"
    assert row_values["Expected delivery date"] == "2026-06-15"
    assert service.mongo_repo.messages[result["message"]["id"]]["metadata_json"]["report_data"]["report_type"] == "purchase_order_draft"


def test_ask_session_returns_sales_order_detail_draft(db_session: Session):
    tenant = _create_tenant(db_session, company="SO Draft Co", email="so-draft@example.com")
    admin = _create_user(
        db_session,
        tenant_id=tenant.id,
        email="so-draft-admin@example.com",
        role=UserRole.TENANT_ADMIN,
    )
    db_session.commit()

    service = _assistant_service(db_session)
    session = service.create_session(tenant_id=tenant.id, user_id=admin.id, title="SO Draft")

    result = service.ask_session(
        tenant_id=tenant.id,
        user_id=admin.id,
        role=UserRole.TENANT_ADMIN,
        session_id=session["id"],
        question=(
            "Draft a sales order for 12 units of Caffeine Body Scrub for customer Glow Retail. "
            "Use these field details: - Customer: Glow Retail - Product: Caffeine Body Scrub "
            "- SKU: MCA-BC-001 - Quantity: 12 - Warehouse: Main Warehouse "
            "- Expected ship date: 2026-06-18 - Unit price: 180.00 - Notes: Priority customer order."
        ),
    )

    assert result["report_data"]["report_type"] == "sales_order_draft"
    assert result["report_data"]["action_url"] == "/sales/new"
    row_values = {row["field"]: row["draft_value"] for row in result["report_data"]["rows"]}
    assert row_values["Customer"] == "Glow Retail"
    assert row_values["Product"] == "Caffeine Body Scrub"
    assert row_values["Quantity"] == "12"
    assert row_values["Expected ship date"] == "2026-06-18"


def test_ask_session_returns_sales_return_detail_draft(db_session: Session):
    tenant = _create_tenant(db_session, company="Return Draft Co", email="return-draft@example.com")
    admin = _create_user(
        db_session,
        tenant_id=tenant.id,
        email="return-draft-admin@example.com",
        role=UserRole.TENANT_ADMIN,
    )
    db_session.commit()

    service = _assistant_service(db_session)
    session = service.create_session(tenant_id=tenant.id, user_id=admin.id, title="Return Draft")

    result = service.ask_session(
        tenant_id=tenant.id,
        user_id=admin.id,
        role=UserRole.TENANT_ADMIN,
        session_id=session["id"],
        question=(
            "Draft a sales return for sales order SO-1001. Use these field details: "
            "- Sales order: SO-1001 - Return number: RET-1001 - Customer: Glow Retail "
            "- Product: Caffeine Body Scrub - SKU: MCA-BC-001 - Returned quantity: 2 "
            "- Warehouse: Main Warehouse - Location: QC-01 - Reason: Damaged on arrival."
        ),
    )

    assert result["report_data"]["report_type"] == "sales_return_draft"
    assert result["report_data"]["action_url"] == "/returns/new"
    row_values = {row["field"]: row["draft_value"] for row in result["report_data"]["rows"]}
    assert row_values["Sales order"] == "SO-1001"
    assert row_values["Returned quantity"] == "2"
    assert row_values["Reason"] == "Damaged on arrival"


def test_ask_session_returns_cycle_count_detail_draft(db_session: Session):
    tenant = _create_tenant(db_session, company="Count Draft Co", email="count-draft@example.com")
    admin = _create_user(
        db_session,
        tenant_id=tenant.id,
        email="count-draft-admin@example.com",
        role=UserRole.TENANT_ADMIN,
    )
    db_session.commit()

    service = _assistant_service(db_session)
    session = service.create_session(tenant_id=tenant.id, user_id=admin.id, title="Cycle Count Draft")

    result = service.ask_session(
        tenant_id=tenant.id,
        user_id=admin.id,
        role=UserRole.TENANT_ADMIN,
        session_id=session["id"],
        question=(
            "Draft a cycle count for Main Warehouse. Use these field details: "
            "- Session name: June audit count - Warehouse: Main Warehouse - Location: A1 "
            "- Products: Caffeine Body Scrub, Rose Toner - Scheduled date: 2026-06-20 "
            "- Reason: Reconciliation mismatch review."
        ),
    )

    assert result["report_data"]["report_type"] == "cycle_count_draft"
    assert result["report_data"]["action_url"] == "/cycle-counts/new"
    row_values = {row["field"]: row["draft_value"] for row in result["report_data"]["rows"]}
    assert row_values["Session name"] == "June audit count"
    assert row_values["Warehouse"] == "Main Warehouse"
    assert row_values["Products"] == "Caffeine Body Scrub, Rose Toner"


def test_ask_session_blocks_off_topic_question(db_session: Session):
    tenant = _create_tenant(db_session, company="Guardrail Co", email="guard@example.com")
    admin = _create_user(
        db_session,
        tenant_id=tenant.id,
        email="guard-admin@example.com",
        role=UserRole.TENANT_ADMIN,
    )
    db_session.commit()

    service = _assistant_service(db_session)
    session = service.create_session(tenant_id=tenant.id, user_id=admin.id, title="Guardrail")
    result = service.ask_session(
        tenant_id=tenant.id,
        user_id=admin.id,
        role=UserRole.TENANT_ADMIN,
        session_id=session["id"],
        question="what is 2+2",
    )

    assert result["is_off_topic"] is True
    assert result["report_data"] is None
    assert result["citations"] == []
    assert result["answer"] == "I can only help with Warelyn Inventory questions."
