"""drop assistant_sessions, assistant_messages, assistant_feedback tables

Data migrated to MongoDB. FAQ documents and chunks remain in MySQL.

Revision ID: 20260601_0025
Revises: 20260531_0024
Create Date: 2026-06-01 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260601_0025"
down_revision: str | None = "20260531_0024"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("SET FOREIGN_KEY_CHECKS = 0")

    op.drop_table("assistant_feedback")
    op.drop_table("assistant_messages")
    op.drop_table("assistant_sessions")

    op.execute("SET FOREIGN_KEY_CHECKS = 1")


def downgrade() -> None:
    op.create_table(
        "assistant_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), server_default="New Assistant Session", nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_assistant_sessions_tenant_id", "assistant_sessions", ["tenant_id"])
    op.create_index("ix_assistant_sessions_user_id", "assistant_sessions", ["user_id"])
    op.create_index("ix_assistant_sessions_tenant_user_created", "assistant_sessions", ["tenant_id", "user_id", "created_at"])

    op.create_table(
        "assistant_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("role", sa.Enum("USER", "ASSISTANT", "SYSTEM", name="assistant_message_role", native_enum=False), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("citations_json", sa.JSON(), nullable=True),
        sa.Column("suggested_actions_json", sa.JSON(), nullable=True),
        sa.Column("usage_json", sa.JSON(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["assistant_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_assistant_messages_tenant_id", "assistant_messages", ["tenant_id"])
    op.create_index("ix_assistant_messages_session_id", "assistant_messages", ["session_id"])
    op.create_index("ix_assistant_messages_user_id", "assistant_messages", ["user_id"])
    op.create_index("ix_assistant_messages_role", "assistant_messages", ["role"])
    op.create_index("ix_assistant_messages_session_created", "assistant_messages", ["session_id", "created_at"])
    op.create_index("ix_assistant_messages_tenant_role", "assistant_messages", ["tenant_id", "role"])

    op.create_table(
        "assistant_feedback",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("value", sa.Enum("UP", "DOWN", name="assistant_feedback_value", native_enum=False), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["message_id"], ["assistant_messages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("message_id", "user_id", name="uq_assistant_feedback_message_user"),
    )
    op.create_index("ix_assistant_feedback_tenant_id", "assistant_feedback", ["tenant_id"])
    op.create_index("ix_assistant_feedback_message_id", "assistant_feedback", ["message_id"])
    op.create_index("ix_assistant_feedback_user_id", "assistant_feedback", ["user_id"])
    op.create_index("ix_assistant_feedback_tenant_value", "assistant_feedback", ["tenant_id", "value"])
