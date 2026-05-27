"""Phase 20: expand DocumentTemplateKey enum (non-native, no schema change needed).

Revision ID: phase20_tpl_keys
Revises: 20260525_0015
Create Date: 2026-05-25
"""
from alembic import op

revision = "phase20_tpl_keys"
down_revision = "20260525_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # DocumentTemplateKey uses native_enum=False (VARCHAR storage).
    # New enum members are stored as plain strings — no ALTER needed.
    pass


def downgrade() -> None:
    pass
