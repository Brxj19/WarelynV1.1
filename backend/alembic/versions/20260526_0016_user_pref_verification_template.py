"""add preferred_verification_template_id to user_preferences

Revision ID: 20260526_0016
Revises: 20260526_0015
Create Date: 2026-05-26
"""
import sqlalchemy as sa
from alembic import op

revision = "20260526_0016"
down_revision = "20260526_0015"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("user_preferences",
        sa.Column("preferred_verification_template_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_up_preferred_verification_template", "user_preferences",
        "document_templates", ["preferred_verification_template_id"], ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_constraint("fk_up_preferred_verification_template", "user_preferences", type_="foreignkey")
    op.drop_column("user_preferences", "preferred_verification_template_id")
