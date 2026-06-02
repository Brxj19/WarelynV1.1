from datetime import datetime

from pydantic import BaseModel, Field


class CitationRead(BaseModel):
    title: str
    source_type: str
    source_uri: str | None = None
    chunk_id: int | None = None
    score: float | None = None


class SuggestedActionRead(BaseModel):
    label: str
    to: str


class FAQAskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)


class FAQSuggestionRead(BaseModel):
    question: str
    description: str | None = None


class FAQAskResponse(BaseModel):
    answer: str
    confidence: str
    confidence_score: float | None = None
    citations: list[CitationRead]
    suggested_actions: list[SuggestedActionRead] = Field(default_factory=list)
    is_off_topic: bool = False


class AssistantSessionCreateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)


class AssistantSessionRead(BaseModel):
    id: int
    tenant_id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AssistantAskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)


class AssistantMessageRead(BaseModel):
    id: int
    tenant_id: int
    session_id: int
    user_id: int | None
    role: str
    content: str
    confidence_score: float | None = None
    citations_json: list[dict] | None = None
    suggested_actions_json: list[dict] | None = None
    usage_json: dict | None = None
    metadata_json: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AssistantSessionDetailRead(BaseModel):
    session: AssistantSessionRead
    messages: list[AssistantMessageRead]


class CopilotReportData(BaseModel):
    report_type: str
    title: str
    columns: list[str]
    row_keys: list[str]
    rows: list[dict]
    total_rows: int
    insights: list[str]
    action_url: str
    query_summary: str | None = None
    workflow_type: str | None = None
    workflow_name: str | None = None


class AssistantAskResponse(BaseModel):
    message: AssistantMessageRead
    confidence: str
    citations: list[CitationRead]
    suggested_actions: list[SuggestedActionRead] = Field(default_factory=list)
    report_data: CopilotReportData | None = None
    is_off_topic: bool = False


class AssistantFeedbackRequest(BaseModel):
    value: str = Field(pattern="^(UP|DOWN)$")
    note: str | None = Field(default=None, max_length=2000)


class AssistantFeedbackRead(BaseModel):
    id: int
    tenant_id: int
    message_id: int
    user_id: int
    value: str
    note: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AssistantTelemetryRead(BaseModel):
    total_requests: int
    avg_latency_ms: float
    total_tokens: int
    abstain_rate_pct: float
    citation_rate_pct: float
