"""Add enterprise commercial, finance, people and governance controls.

Revision ID: 0003_enterprise_control_plane
Revises: 0002_management_controls
"""

from alembic import op

from app.db import Base
from app import models, accounting_models, control_models, enterprise_finance_models, enterprise_admin_models  # noqa: F401

revision = "0003_enterprise_control_plane"
down_revision = "0002_management_controls"
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    bind = op.get_bind()
    for table_name in [
        "notifications",
        "audit_events",
        "document_records",
        "approval_requests",
        "payslips",
        "payroll_runs",
        "employees",
        "bank_transactions",
        "bank_accounts",
        "journal_lines",
        "journal_entries",
        "ledger_accounts",
        "quote_lines",
        "quotes",
    ]:
        table = Base.metadata.tables.get(table_name)
        if table is not None:
            table.drop(bind=bind, checkfirst=True)
