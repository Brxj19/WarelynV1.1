from datetime import datetime

from pydantic import BaseModel


class WorkflowTaskCreate(BaseModel):
    workflow_type: str
    entity_type: str
    entity_id: int
    step_key: str
    title: str
    description: str | None = None
    assigned_role: str
    assigned_to_user_id: int | None = None
    priority: str = "NORMAL"
    action_url: str | None = None
    due_at: datetime | None = None
    metadata_json: dict | None = None


class WorkflowTaskRead(BaseModel):
    id: int
    tenant_id: int
    workflow_type: str
    entity_type: str
    entity_id: int
    step_key: str
    title: str
    description: str | None
    assigned_role: str
    assigned_to_user_id: int | None
    status: str
    priority: str
    action_url: str | None
    created_by: int | None
    completed_by: int | None
    created_at: datetime
    due_at: datetime | None
    completed_at: datetime | None
    metadata_json: dict | None

    model_config = {"from_attributes": True}


class WorkflowTaskComplete(BaseModel):
    notes: str | None = None


class WorkflowEventRead(BaseModel):
    id: int
    tenant_id: int
    event_type: str
    entity_type: str
    entity_id: int
    actor_user_id: int | None
    payload_json: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}
