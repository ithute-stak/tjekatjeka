import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()


class Quote(Base):
    __tablename__ = "quotes"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"))
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    quote_no: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    subtotal: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False, default=0)
    tax_amount: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False, default=0)
    total_amount: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    quote_date: Mapped[date] = mapped_column(Date, default=date.today)
    valid_until: Mapped[date | None] = mapped_column(Date)
    converted_invoice_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("customer_invoices.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class QuoteLine(Base):
    __tablename__ = "quote_lines"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    quote_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False)
    description: Mapped[str] = mapped_column(String(240), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(16, 4), nullable=False)
    unit: Mapped[str] = mapped_column(String(30), default="each")
    unit_price: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False)
    line_total: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False)


class LedgerAccount(Base):
    __tablename__ = "ledger_accounts"
    __table_args__ = (UniqueConstraint("code", name="uq_ledger_account_code"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    account_type: Mapped[str] = mapped_column(String(30), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class JournalEntry(Base):
    __tablename__ = "journal_entries"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    reference: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(240), nullable=False)
    entry_date: Mapped[date] = mapped_column(Date, default=date.today)
    source_type: Mapped[str | None] = mapped_column(String(50))
    source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    posted_by: Mapped[str | None] = mapped_column(String(320))
    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class JournalLine(Base):
    __tablename__ = "journal_lines"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    entry_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ledger_accounts.id"), nullable=False)
    debit: Mapped[float] = mapped_column(Numeric(16, 2), default=0)
    credit: Mapped[float] = mapped_column(Numeric(16, 2), default=0)
    memo: Mapped[str | None] = mapped_column(String(240))


class BankAccount(Base):
    __tablename__ = "bank_accounts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    bank_name: Mapped[str] = mapped_column(String(140), nullable=False)
    account_mask: Mapped[str] = mapped_column(String(60), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="LSL")
    opening_balance: Mapped[float] = mapped_column(Numeric(16, 2), default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class BankTransaction(Base):
    __tablename__ = "bank_transactions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    bank_account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bank_accounts.id"), nullable=False)
    transaction_date: Mapped[date] = mapped_column(Date, default=date.today)
    description: Mapped[str] = mapped_column(String(240), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(100))
    amount: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    reconciled: Mapped[bool] = mapped_column(Boolean, default=False)
    reconciled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    journal_entry_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("journal_entries.id"))
