"""Create Tjekatjeka core business schema.

Revision ID: 0001_tjekatjeka_core
Revises:
"""

from alembic import op

from app.db import Base
from app import models  # noqa: F401

revision = "0001_tjekatjeka_core"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
