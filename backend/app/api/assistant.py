from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_roles, require_super_admin
from app.models.auth import UserRole
from app.schemas.assistant import (
    AssistantAskRequest,
    AssistantAskResponse,
    AssistantFeedbackRead,
    AssistantFeedbackRequest,
    AssistantMessageRead,
    AssistantSessionCreateRequest,
    AssistantSessionDetailRead,
    AssistantSessionRead,
    AssistantTelemetryRead,
    CopilotReportData,
    FAQAskRequest,
    FAQAskResponse,
    FAQSuggestionRead,
)
from app.services.assistant import AssistantService
from app.services.auth import UserContext

router = APIRouter(tags=["assistant"])

faq_roles = (
    UserRole.TENANT_ADMIN,
    UserRole.INVENTORY_MANAGER,
    UserRole.SALES_STAFF,
    UserRole.PURCHASE_STAFF,
    UserRole.VIEWER,
)

copilot_roles = (UserRole.TENANT_ADMIN,)


@router.get("/faq/suggestions", response_model=list[FAQSuggestionRead])
def faq_suggestions(
    context: UserContext = Depends(require_roles(*faq_roles)),
    db: Session = Depends(get_db),
) -> list[FAQSuggestionRead]:
    service = AssistantService(db)
    return [FAQSuggestionRead(**row) for row in service.faq_suggestions(context.role)]


@router.post("/admin/reindex", response_model=dict)
def admin_reindex(
    context: UserContext = Depends(require_super_admin),
    db: Session = Depends(get_db),
) -> dict:
    return AssistantService(db).reindex_global_knowledge()


@router.post("/faq/ask", response_model=FAQAskResponse)
def ask_faq(
    payload: FAQAskRequest,
    context: UserContext = Depends(require_roles(*faq_roles)),
    db: Session = Depends(get_db),
) -> FAQAskResponse:
    service = AssistantService(db)
    service.ensure_bootstrap_index()
    result = service.ask_faq(
        tenant_id=context.tenant_id,
        user_id=context.user.id,
        role=context.role,
        question=payload.question,
    )
    return FAQAskResponse(
        answer=result["answer"],
        confidence=result["confidence"],
        confidence_score=result.get("confidence_score"),
        citations=result["citations"],
        suggested_actions=result["suggested_actions"],
        is_off_topic=result.get("is_off_topic", False),
    )


@router.get("/assistant/sessions", response_model=list[AssistantSessionRead])
def list_sessions(
    context: UserContext = Depends(require_roles(*copilot_roles)),
    db: Session = Depends(get_db),
) -> list[AssistantSessionRead]:
    sessions = AssistantService(db).list_sessions(
        tenant_id=context.tenant_id,
        user_id=context.user.id,
    )
    return [AssistantSessionRead.model_validate(s) for s in sessions]


@router.post("/assistant/sessions", response_model=AssistantSessionRead)
def create_session(
    payload: AssistantSessionCreateRequest,
    context: UserContext = Depends(require_roles(*copilot_roles)),
    db: Session = Depends(get_db),
) -> AssistantSessionRead:
    session = AssistantService(db).create_session(
        tenant_id=context.tenant_id,
        user_id=context.user.id,
        title=payload.title,
    )
    return AssistantSessionRead.model_validate(session)


@router.get("/assistant/sessions/{session_id}", response_model=AssistantSessionDetailRead)
def session_detail(
    session_id: int,
    context: UserContext = Depends(require_roles(*copilot_roles)),
    db: Session = Depends(get_db),
) -> AssistantSessionDetailRead:
    detail = AssistantService(db).get_session_detail(
        tenant_id=context.tenant_id,
        user_id=context.user.id,
        session_id=session_id,
    )
    return AssistantSessionDetailRead(
        session=AssistantSessionRead.model_validate(detail["session"]),
        messages=[AssistantMessageRead.model_validate(row) for row in detail["messages"]],
    )


@router.post("/assistant/sessions/{session_id}/ask", response_model=AssistantAskResponse)
def ask_session(
    session_id: int,
    payload: AssistantAskRequest,
    context: UserContext = Depends(require_roles(*copilot_roles)),
    db: Session = Depends(get_db),
) -> AssistantAskResponse:
    service = AssistantService(db)
    service.ensure_bootstrap_index()
    result = service.ask_session(
        tenant_id=context.tenant_id,
        user_id=context.user.id,
        role=context.role,
        session_id=session_id,
        question=payload.question,
    )
    return AssistantAskResponse(
        message=AssistantMessageRead.model_validate(result["message"]),
        confidence=result["confidence"],
        citations=result["citations"],
        suggested_actions=result["suggested_actions"],
        report_data=CopilotReportData(**result["report_data"]) if result.get("report_data") else None,
        is_off_topic=result.get("is_off_topic", False),
    )


@router.post("/assistant/messages/{message_id}/feedback", response_model=AssistantFeedbackRead)
def feedback(
    message_id: int,
    payload: AssistantFeedbackRequest,
    context: UserContext = Depends(require_roles(*copilot_roles)),
    db: Session = Depends(get_db),
) -> AssistantFeedbackRead:
    feedback_row = AssistantService(db).add_feedback(
        tenant_id=context.tenant_id,
        user_id=context.user.id,
        message_id=message_id,
        value=payload.value,
        note=payload.note,
    )
    return AssistantFeedbackRead.model_validate(feedback_row)


@router.delete("/assistant/sessions/{session_id}", status_code=204)
def delete_session(
    session_id: int,
    context: UserContext = Depends(require_roles(*copilot_roles)),
    db: Session = Depends(get_db),
) -> None:
    AssistantService(db).delete_session(
        tenant_id=context.tenant_id,
        user_id=context.user.id,
        session_id=session_id,
    )


@router.get("/assistant/telemetry", response_model=AssistantTelemetryRead)
def telemetry(
    context: UserContext = Depends(require_roles(*copilot_roles)),
    db: Session = Depends(get_db),
) -> AssistantTelemetryRead:
    data = AssistantService(db).telemetry(tenant_id=context.tenant_id)
    return AssistantTelemetryRead(**data)
