"""Add customer accounts, production standards, measurements and deliveries.

Revision ID: 0002_management_controls
Revises: 0001_tjekatjeka_core
"""

from alembic import op
from app.db import Base
from app import accounting_models, control_models  # noqa: F401

revision = "0002_management_controls"
down_revision = "0001_tjekatjeka_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    bind = op.get_bind()
    for table_name in [
        "delivery_orders",
        "aluminium_measurements",
        "brick_recipe_inputs",
        "brick_recipes",
        "supplier_payments",
        "supplier_bills",
        "customer_payments",
        "customer_invoices",
    ]:
        table = Base.metadata.tables.get(table_name)
        if table is not None:
            table.drop(bind=bind, checkfirst=True)
