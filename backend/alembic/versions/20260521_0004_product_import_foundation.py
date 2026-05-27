"""product import foundation

Revision ID: 20260521_0004
Revises: 20260521_0003
Create Date: 2026-05-21 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260521_0004"
down_revision: str | None = "20260521_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

product_import_mode = sa.Enum("create_only", "update_existing", "upsert", name="product_import_mode", native_enum=False)
import_job_status = sa.Enum("UPLOADED", "VALIDATING", "VALIDATED", "HAS_ERRORS", "COMMITTED", "CANCELLED", name="import_job_status", native_enum=False)
import_row_status = sa.Enum("PENDING", "VALID", "ERROR", "WARNING", "SKIPPED", "CREATED", "UPDATED", name="import_row_status", native_enum=False)


def upgrade() -> None:
    op.create_table(
        "import_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("import_type", sa.String(length=80), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("mode", product_import_mode, nullable=False),
        sa.Column("status", import_job_status, nullable=False),
        sa.Column("total_rows", sa.Integer(), nullable=False),
        sa.Column("valid_rows", sa.Integer(), nullable=False),
        sa.Column("error_rows", sa.Integer(), nullable=False),
        sa.Column("warning_rows", sa.Integer(), nullable=False),
        sa.Column("created_count", sa.Integer(), nullable=False),
        sa.Column("updated_count", sa.Integer(), nullable=False),
        sa.Column("skipped_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("committed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ["id", "tenant_id", "created_by", "import_type", "mode", "status", "created_at"]:
        op.create_index(op.f(f"ix_import_jobs_{column}"), "import_jobs", [column], unique=False)
    op.create_index("ix_import_jobs_tenant_status", "import_jobs", ["tenant_id", "status"], unique=False)

    op.create_table(
        "import_job_rows",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("raw_data", sa.JSON(), nullable=False),
        sa.Column("normalized_data", sa.JSON(), nullable=True),
        sa.Column("status", import_row_status, nullable=False),
        sa.Column("errors", sa.JSON(), nullable=False),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("existing_product_id", sa.Integer(), nullable=True),
        sa.Column("created_product_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_product_id"], ["products.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["existing_product_id"], ["products.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["job_id"], ["import_jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "job_id", "row_number", name="uq_import_rows_tenant_job_row"),
    )
    for column in ["id", "tenant_id", "job_id", "status", "existing_product_id", "created_product_id", "created_at"]:
        op.create_index(op.f(f"ix_import_job_rows_{column}"), "import_job_rows", [column], unique=False)
    op.create_index("ix_import_rows_tenant_job_status", "import_job_rows", ["tenant_id", "job_id", "status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_import_rows_tenant_job_status", table_name="import_job_rows")
    for column in ["created_at", "created_product_id", "existing_product_id", "status", "job_id", "tenant_id", "id"]:
        op.drop_index(op.f(f"ix_import_job_rows_{column}"), table_name="import_job_rows")
    op.drop_table("import_job_rows")
    op.drop_index("ix_import_jobs_tenant_status", table_name="import_jobs")
    for column in ["created_at", "status", "mode", "import_type", "created_by", "tenant_id", "id"]:
        op.drop_index(op.f(f"ix_import_jobs_{column}"), table_name="import_jobs")
    op.drop_table("import_jobs")
