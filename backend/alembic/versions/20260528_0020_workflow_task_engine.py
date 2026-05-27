"""Workflow events and tasks tables

Revision ID: 20260528_0020
Revises: 20260526_0018
Create Date: 2026-05-28
"""
import sqlalchemy as sa
from alembic import op

revision = "20260528_0020"
down_revision = "20260526_0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workflow_events",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("tenant_id", sa.Integer, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.Integer, nullable=False),
        sa.Column("actor_user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("payload_json", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_workflow_events_tenant_type_created", "workflow_events", ["tenant_id", "event_type", "created_at"])

    op.create_table(
        "workflow_tasks",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("tenant_id", sa.Integer, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workflow_type", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.Integer, nullable=False),
        sa.Column("step_key", sa.String(100), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("assigned_role", sa.String(50), nullable=False),
        sa.Column("assigned_to_user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="OPEN"),
        sa.Column("priority", sa.String(20), nullable=False, server_default="NORMAL"),
        sa.Column("action_url", sa.String(500), nullable=True),
        sa.Column("created_by", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("completed_by", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", sa.JSON, nullable=True),
    )
    op.create_index("ix_workflow_tasks_role_status", "workflow_tasks", ["tenant_id", "assigned_role", "status"])
    op.create_index("ix_workflow_tasks_user_status", "workflow_tasks", ["tenant_id", "assigned_to_user_id", "status"])
    op.create_index("ix_workflow_tasks_entity", "workflow_tasks", ["tenant_id", "entity_type", "entity_id"])


def downgrade() -> None:
    op.drop_index("ix_workflow_tasks_entity", table_name="workflow_tasks")
    op.drop_index("ix_workflow_tasks_user_status", table_name="workflow_tasks")
    op.drop_index("ix_workflow_tasks_role_status", table_name="workflow_tasks")
    op.drop_table("workflow_tasks")
    op.drop_index("ix_workflow_events_tenant_type_created", table_name="workflow_events")
    op.drop_table("workflow_events")
