"""add tenant-level template preference fields

Revision ID: 20260531_0023
Revises: 20260529_0022
Create Date: 2026-05-31 18:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260531_0023"
down_revision: str | None = "20260529_0022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("tenant_settings", sa.Column("preferred_invoice_template_id", sa.Integer(), nullable=True))
    op.add_column("tenant_settings", sa.Column("preferred_bill_template_id", sa.Integer(), nullable=True))
    op.add_column("tenant_settings", sa.Column("preferred_invoice_email_template_id", sa.Integer(), nullable=True))
    op.add_column("tenant_settings", sa.Column("preferred_bill_email_template_id", sa.Integer(), nullable=True))
    op.add_column("tenant_settings", sa.Column("preferred_verification_template_id", sa.Integer(), nullable=True))

    op.create_index("ix_tenant_settings_preferred_invoice_template_id", "tenant_settings", ["preferred_invoice_template_id"])
    op.create_index("ix_tenant_settings_preferred_bill_template_id", "tenant_settings", ["preferred_bill_template_id"])
    op.create_index("ix_tenant_settings_preferred_invoice_email_template_id", "tenant_settings", ["preferred_invoice_email_template_id"])
    op.create_index("ix_tenant_settings_preferred_bill_email_template_id", "tenant_settings", ["preferred_bill_email_template_id"])
    op.create_index("ix_tenant_settings_preferred_verification_template_id", "tenant_settings", ["preferred_verification_template_id"])

    op.create_foreign_key(
        "fk_ts_preferred_invoice_template",
        "tenant_settings",
        "document_templates",
        ["preferred_invoice_template_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_ts_preferred_bill_template",
        "tenant_settings",
        "document_templates",
        ["preferred_bill_template_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_ts_preferred_invoice_email_template",
        "tenant_settings",
        "document_templates",
        ["preferred_invoice_email_template_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_ts_preferred_bill_email_template",
        "tenant_settings",
        "document_templates",
        ["preferred_bill_email_template_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_ts_preferred_verification_template",
        "tenant_settings",
        "document_templates",
        ["preferred_verification_template_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_ts_preferred_verification_template", "tenant_settings", type_="foreignkey")
    op.drop_constraint("fk_ts_preferred_bill_email_template", "tenant_settings", type_="foreignkey")
    op.drop_constraint("fk_ts_preferred_invoice_email_template", "tenant_settings", type_="foreignkey")
    op.drop_constraint("fk_ts_preferred_bill_template", "tenant_settings", type_="foreignkey")
    op.drop_constraint("fk_ts_preferred_invoice_template", "tenant_settings", type_="foreignkey")

    op.drop_index("ix_tenant_settings_preferred_verification_template_id", table_name="tenant_settings")
    op.drop_index("ix_tenant_settings_preferred_bill_email_template_id", table_name="tenant_settings")
    op.drop_index("ix_tenant_settings_preferred_invoice_email_template_id", table_name="tenant_settings")
    op.drop_index("ix_tenant_settings_preferred_bill_template_id", table_name="tenant_settings")
    op.drop_index("ix_tenant_settings_preferred_invoice_template_id", table_name="tenant_settings")

    op.drop_column("tenant_settings", "preferred_verification_template_id")
    op.drop_column("tenant_settings", "preferred_bill_email_template_id")
    op.drop_column("tenant_settings", "preferred_invoice_email_template_id")
    op.drop_column("tenant_settings", "preferred_bill_template_id")
    op.drop_column("tenant_settings", "preferred_invoice_template_id")
