"""add rag faq and assistant foundation tables

Revision ID: 20260531_0024
Revises: 20260531_0023
Create Date: 2026-05-31 22:15:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260531_0024"
down_revision: str | None = "20260531_0023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "faq_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=True),
        sa.Column("slug", sa.String(length=180), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.Enum("DOC", "WORKFLOW", "PRODUCT", "SYSTEM", name="knowledge_source_type", native_enum=False), nullable=False),
        sa.Column("source_uri", sa.String(length=500), nullable=True),
        sa.Column("body_text", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "slug", name="uq_faq_documents_tenant_slug"),
    )
    op.create_index("ix_faq_documents_tenant_id", "faq_documents", ["tenant_id"])
    op.create_index("ix_faq_documents_checksum", "faq_documents", ["checksum"])
    op.create_index("ix_faq_documents_tenant_source", "faq_documents", ["tenant_id", "source_type"])

    op.create_table(
        "faq_chunks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=True),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("searchable_text", sa.Text(), nullable=False),
        sa.Column("embedding", sa.JSON(), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["faq_documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "chunk_index", name="uq_faq_chunks_document_index"),
    )
    op.create_index("ix_faq_chunks_tenant_id", "faq_chunks", ["tenant_id"])
    op.create_index("ix_faq_chunks_document_id", "faq_chunks", ["document_id"])
    op.create_index("ix_faq_chunks_tenant_document", "faq_chunks", ["tenant_id", "document_id"])
    op.create_index("ix_faq_chunks_tenant_created", "faq_chunks", ["tenant_id", "created_at"])

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


def downgrade() -> None:
    op.drop_index("ix_assistant_feedback_tenant_value", table_name="assistant_feedback")
    op.drop_index("ix_assistant_feedback_user_id", table_name="assistant_feedback")
    op.drop_index("ix_assistant_feedback_message_id", table_name="assistant_feedback")
    op.drop_index("ix_assistant_feedback_tenant_id", table_name="assistant_feedback")
    op.drop_table("assistant_feedback")

    op.drop_index("ix_assistant_messages_tenant_role", table_name="assistant_messages")
    op.drop_index("ix_assistant_messages_session_created", table_name="assistant_messages")
    op.drop_index("ix_assistant_messages_role", table_name="assistant_messages")
    op.drop_index("ix_assistant_messages_user_id", table_name="assistant_messages")
    op.drop_index("ix_assistant_messages_session_id", table_name="assistant_messages")
    op.drop_index("ix_assistant_messages_tenant_id", table_name="assistant_messages")
    op.drop_table("assistant_messages")

    op.drop_index("ix_assistant_sessions_tenant_user_created", table_name="assistant_sessions")
    op.drop_index("ix_assistant_sessions_user_id", table_name="assistant_sessions")
    op.drop_index("ix_assistant_sessions_tenant_id", table_name="assistant_sessions")
    op.drop_table("assistant_sessions")

    op.drop_index("ix_faq_chunks_tenant_created", table_name="faq_chunks")
    op.drop_index("ix_faq_chunks_tenant_document", table_name="faq_chunks")
    op.drop_index("ix_faq_chunks_document_id", table_name="faq_chunks")
    op.drop_index("ix_faq_chunks_tenant_id", table_name="faq_chunks")
    op.drop_table("faq_chunks")

    op.drop_index("ix_faq_documents_tenant_source", table_name="faq_documents")
    op.drop_index("ix_faq_documents_checksum", table_name="faq_documents")
    op.drop_index("ix_faq_documents_tenant_id", table_name="faq_documents")
    op.drop_table("faq_documents")
