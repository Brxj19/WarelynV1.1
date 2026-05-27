"""user preferences template preference fields

Revision ID: 20260526_0015
Revises: phase20_tpl_keys
Create Date: 2026-05-26
"""
import sqlalchemy as sa
from alembic import op

revision = "20260526_0015"
down_revision = "phase20_tpl_keys"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("user_preferences",
        sa.Column("preferred_invoice_template_id", sa.Integer(), nullable=True))
    op.add_column("user_preferences",
        sa.Column("preferred_bill_template_id", sa.Integer(), nullable=True))
    op.add_column("user_preferences",
        sa.Column("preferred_invoice_email_template_id", sa.Integer(), nullable=True))
    op.add_column("user_preferences",
        sa.Column("preferred_bill_email_template_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_up_preferred_invoice_template", "user_preferences",
        "document_templates", ["preferred_invoice_template_id"], ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_up_preferred_bill_template", "user_preferences",
        "document_templates", ["preferred_bill_template_id"], ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_up_preferred_invoice_email_template", "user_preferences",
        "document_templates", ["preferred_invoice_email_template_id"], ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_up_preferred_bill_email_template", "user_preferences",
        "document_templates", ["preferred_bill_email_template_id"], ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_constraint("fk_up_preferred_invoice_template", "user_preferences", type_="foreignkey")
    op.drop_constraint("fk_up_preferred_bill_template", "user_preferences", type_="foreignkey")
    op.drop_constraint("fk_up_preferred_invoice_email_template", "user_preferences", type_="foreignkey")
    op.drop_constraint("fk_up_preferred_bill_email_template", "user_preferences", type_="foreignkey")
    op.drop_column("user_preferences", "preferred_invoice_template_id")
    op.drop_column("user_preferences", "preferred_bill_template_id")
    op.drop_column("user_preferences", "preferred_invoice_email_template_id")
    op.drop_column("user_preferences", "preferred_bill_email_template_id")
