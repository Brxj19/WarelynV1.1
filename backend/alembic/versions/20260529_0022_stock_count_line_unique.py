"""add stock count line uniqueness guard

Revision ID: 20260529_0022
Revises: 20260528_0021
Create Date: 2026-05-29 12:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260529_0022"
down_revision: str | None = "20260528_0021"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_stock_count_lines_session_product_location",
        "stock_count_lines",
        ["tenant_id", "session_id", "product_id", "location_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_stock_count_lines_session_product_location", "stock_count_lines", type_="unique")
