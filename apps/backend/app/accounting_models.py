import uuid
from datetime import date, datetime
from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()


class CustomerInvoice(Base):
    __tablename__ = "customer_invoices"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"))
    invoice_no: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(240), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="open")
    invoice_date: Mapped[date] = mapped_column(Date, default=date.today)
    due_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CustomerPayment(Base):
    __tablename__ = "customer_payments"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("customer_invoices.id"))
    amount: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False)
    method: Mapped[str] = mapped_column(String(40), default="bank")
    reference: Mapped[str | None] = mapped_column(String(100))
    payment_date: Mapped[date] = mapped_column(Date, default=date.today)
    notes: Mapped[str | None] = mapped_column(Text)


class SupplierBill(Base):
    __tablename__ = "supplier_bills"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"))
    bill_no: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(240), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="open")
    bill_date: Mapped[date] = mapped_column(Date, default=date.today)
    due_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SupplierPayment(Base):
    __tablename__ = "supplier_payments"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    bill_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("supplier_bills.id"))
    amount: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False)
    method: Mapped[str] = mapped_column(String(40), default="bank")
    reference: Mapped[str | None] = mapped_column(String(100))
    payment_date: Mapped[date] = mapped_column(Date, default=date.today)
    notes: Mapped[str | None] = mapped_column(Text)
