from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.assistant import AssistantFeedbackValue, AssistantMessage, AssistantMessageRole, FAQChunk, FAQDocument, KnowledgeSourceType
from app.models.audit import AuditLog
from app.models.auth import Tenant, TenantStatus, User, UserRole, UserStatus
from app.services.assistant import AssistantService


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

    service = AssistantService(db_session)
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
        session_id=session.id,
        question="What should I do first today?",
    )
    assert ask_result["message"].role == AssistantMessageRole.ASSISTANT
    assert ask_result["confidence"] == "HIGH"
    assert ask_result["citations"]
    assert ask_result["suggested_actions"]

    feedback = service.add_feedback(
        tenant_id=tenant.id,
        user_id=admin.id,
        message_id=ask_result["message"].id,
        value=AssistantFeedbackValue.UP.value,
        note="Useful and grounded",
    )
    assert feedback.value == AssistantFeedbackValue.UP

    detail = service.get_session_detail(tenant_id=tenant.id, user_id=admin.id, session_id=session.id)
    assert len(detail["messages"]) == 2
    assert detail["messages"][-1].content.startswith("Prioritize OPEN tasks")

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

    stored_assistant_messages = list(
        db_session.scalars(
            select(AssistantMessage).where(AssistantMessage.tenant_id == tenant.id, AssistantMessage.session_id == session.id)
        )
    )
    assert any(message.role == AssistantMessageRole.ASSISTANT for message in stored_assistant_messages)
