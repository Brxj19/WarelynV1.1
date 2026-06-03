"""Shared helper for running Alembic migrations before standalone seed scripts."""

from __future__ import annotations

import os

from alembic import command
from alembic.config import Config as AlembicConfig


def upgrade_database() -> None:
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    alembic_cfg = AlembicConfig(os.path.join(backend_dir, "alembic.ini"))
    alembic_cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))
    command.upgrade(alembic_cfg, "head")
