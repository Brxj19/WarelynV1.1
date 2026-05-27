"""Add purpose, template_code, is_system, created_by, cloned_from, description to document_templates

Revision ID: 20260526_0017
Revises: 20260526_0016
Create Date: 2026-05-26
"""
import sqlalchemy as sa
from alembic import op

revision = "20260526_0017"
down_revision = "20260526_0016"
branch_labels = None
depends_on = None

_KEY_TO_PURPOSE = {
    "EMAIL_VERIFICATION": "EMAIL_VERIFICATION",
    "EMAIL_VERIFICATION_MODERN": "EMAIL_VERIFICATION",
    "EMAIL_VERIFICATION_MINIMAL": "EMAIL_VERIFICATION",
    "INVOICE_SEND": "INVOICE_EMAIL",
    "INVOICE_SEND_MODERN": "INVOICE_EMAIL",
    "INVOICE_SEND_MINIMAL": "INVOICE_EMAIL",
    "INVOICE_SEND_FORMAL": "INVOICE_EMAIL",
    "BILL_SEND": "BILL_EMAIL",
    "BILL_SEND_MODERN": "BILL_EMAIL",
    "BILL_SEND_MINIMAL": "BILL_EMAIL",
    "BILL_SEND_FORMAL": "BILL_EMAIL",
    "PDF_INVOICE": "INVOICE_PDF",
    "PDF_INVOICE_MODERN": "INVOICE_PDF",
    "PDF_INVOICE_MINIMAL": "INVOICE_PDF",
    "PDF_INVOICE_BOLD": "INVOICE_PDF",
    "PDF_INVOICE_WARM": "INVOICE_PDF",
    "PDF_BILL": "BILL_PDF",
    "PDF_BILL_MODERN": "BILL_PDF",
    "PDF_BILL_MINIMAL": "BILL_PDF",
    "PDF_BILL_BOLD": "BILL_PDF",
    "PDF_BILL_WARM": "BILL_PDF",
}


def upgrade():
    op.add_column("document_templates", sa.Column("purpose", sa.String(50), nullable=True))
    op.add_column("document_templates", sa.Column("template_code", sa.String(100), nullable=True))
    op.add_column("document_templates", sa.Column("is_system", sa.Boolean(), nullable=True, server_default=sa.text("0")))
    op.add_column("document_templates", sa.Column("created_by", sa.Integer(), nullable=True))
    op.add_column("document_templates", sa.Column("cloned_from_template_id", sa.Integer(), nullable=True))
    op.add_column("document_templates", sa.Column("description", sa.String(500), nullable=True))

    # Populate purpose and template_code from existing template_key values
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, template_key FROM document_templates WHERE template_key IS NOT NULL"))
    for row in rows:
        purpose = _KEY_TO_PURPOSE.get(row[1], "INVOICE_PDF")
        conn.execute(
            sa.text("UPDATE document_templates SET purpose = :purpose, template_code = :code, is_system = 1 WHERE id = :id"),
            {"purpose": purpose, "code": row[1], "id": row[0]},
        )

    # Make purpose and template_code NOT NULL now that they're populated
    op.alter_column("document_templates", "purpose", nullable=False, existing_type=sa.String(50))
    op.alter_column("document_templates", "template_code", nullable=False, existing_type=sa.String(100))
    op.alter_column("document_templates", "is_system", nullable=False, existing_type=sa.Boolean(), server_default=None)

    # Make template_key nullable (was NOT NULL before)
    op.alter_column("document_templates", "template_key", nullable=True, existing_type=sa.String(50))

    # Add foreign keys
    op.create_foreign_key(
        "fk_dt_created_by", "document_templates",
        "users", ["created_by"], ["id"], ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_dt_cloned_from", "document_templates",
        "document_templates", ["cloned_from_template_id"], ["id"], ondelete="SET NULL",
    )

    # Add index on purpose
    op.create_index("ix_document_templates_purpose", "document_templates", ["purpose"])

    # Drop old unique constraint and add new one on (tenant_id, template_code)
    # The old constraint was on (tenant_id, channel, template_key)
    try:
        op.drop_constraint("uq_document_templates_tenant_channel_key", "document_templates", type_="unique")
    except Exception:
        pass
    op.create_unique_constraint("uq_document_templates_tenant_code", "document_templates", ["tenant_id", "template_code"])


def downgrade():
    op.drop_constraint("uq_document_templates_tenant_code", "document_templates", type_="unique")
    try:
        op.create_unique_constraint("uq_document_templates_tenant_channel_key", "document_templates", ["tenant_id", "channel", "template_key"])
    except Exception:
        pass
    op.drop_index("ix_document_templates_purpose", "document_templates")
    op.drop_constraint("fk_dt_cloned_from", "document_templates", type_="foreignkey")
    op.drop_constraint("fk_dt_created_by", "document_templates", type_="foreignkey")
    op.alter_column("document_templates", "template_key", nullable=False, existing_type=sa.String(50))
    op.drop_column("document_templates", "description")
    op.drop_column("document_templates", "cloned_from_template_id")
    op.drop_column("document_templates", "created_by")
    op.drop_column("document_templates", "is_system")
    op.drop_column("document_templates", "template_code")
    op.drop_column("document_templates", "purpose")
