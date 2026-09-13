import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()


class Profile(Base):
    __tablename__ = "profiles"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    auth_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False)
    email_snapshot: Mapped[str | None] = mapped_column(String(320))
    role: Mapped[str] = mapped_column(String(40), default="admin")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Branch(Base):
    __tablename__ = "branches"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    division: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Material(Base):
    __tablename__ = "materials"
    __table_args__ = (UniqueConstraint("branch_id", "code", name="uq_material_branch_code"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=True)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    category: Mapped[str] = mapped_column(String(60), nullable=False)
    unit: Mapped[str] = mapped_column(String(30), nullable=False)
    quantity_on_hand: Mapped[float] = mapped_column(Numeric(16, 4), default=0)
    average_unit_cost: Mapped[float] = mapped_column(Numeric(16, 4), default=0)
    reorder_level: Mapped[float] = mapped_column(Numeric(16, 4), default=0)


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (UniqueConstraint("branch_id", "code", name="uq_product_branch_code"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    branch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    unit: Mapped[str] = mapped_column(String(30), default="each")
    quantity_on_hand: Mapped[float] = mapped_column(Numeric(16, 4), default=0)
    selling_price: Mapped[float] = mapped_column(Numeric(16, 2), default=0)


class Supplier(Base):
    __tablename__ = "suppliers"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(180), unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(60))
    email: Mapped[str | None] = mapped_column(String(320))


class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(60))
    email: Mapped[str | None] = mapped_column(String(320))


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    material_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("materials.id"), nullable=False)
    movement_type: Mapped[str] = mapped_column(String(40), nullable=False)
    quantity_delta: Mapped[float] = mapped_column(Numeric(16, 4), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Purchase(Base):
    __tablename__ = "purchases"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"))
    material_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("materials.id"))
    supplier_name: Mapped[str] = mapped_column(String(180), nullable=False)
    item_name: Mapped[str] = mapped_column(String(180), nullable=False)
    category: Mapped[str] = mapped_column(String(60), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(16, 4), nullable=False)
    unit: Mapped[str] = mapped_column(String(30), nullable=False)
    unit_cost: Mapped[float] = mapped_column(Numeric(16, 4), nullable=False)
    total_cost: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(100))
    purchase_date: Mapped[date] = mapped_column(Date, default=date.today)


class Expense(Base):
    __tablename__ = "expenses"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"))
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(String(240), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(100))
    expense_date: Mapped[date] = mapped_column(Date, default=date.today)


class ProductionBatch(Base):
    __tablename__ = "production_batches"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    branch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    batch_no: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    produced_quantity: Mapped[float] = mapped_column(Numeric(16, 4), nullable=False)
    rejected_quantity: Mapped[float] = mapped_column(Numeric(16, 4), default=0)
    good_quantity: Mapped[float] = mapped_column(Numeric(16, 4), nullable=False)
    material_cost: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False)
    electricity_cost: Mapped[float] = mapped_column(Numeric(16, 2), default=0)
    water_cost: Mapped[float] = mapped_column(Numeric(16, 2), default=0)
    labour_cost: Mapped[float] = mapped_column(Numeric(16, 2), default=0)
    machine_cost: Mapped[float] = mapped_column(Numeric(16, 2), default=0)
    fuel_cost: Mapped[float] = mapped_column(Numeric(16, 2), default=0)
    other_cost: Mapped[float] = mapped_column(Numeric(16, 2), default=0)
    total_cost: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False)
    cost_per_good_unit: Mapped[float] = mapped_column(Numeric(16, 4), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    production_date: Mapped[date] = mapped_column(Date, default=date.today)


class ProductionInput(Base):
    __tablename__ = "production_inputs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    batch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("production_batches.id"), nullable=False)
    material_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("materials.id"), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(16, 4), nullable=False)
    unit_cost: Mapped[float] = mapped_column(Numeric(16, 4), nullable=False)
    total_cost: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False)


class AluminiumJob(Base):
    __tablename__ = "aluminium_jobs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    branch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    job_no: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    customer_name: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    quote_amount: Mapped[float] = mapped_column(Numeric(16, 2), default=0)
    material_cost: Mapped[float] = mapped_column(Numeric(16, 2), default=0)
    labour_cost: Mapped[float] = mapped_column(Numeric(16, 2), default=0)
    transport_cost: Mapped[float] = mapped_column(Numeric(16, 2), default=0)
    other_cost: Mapped[float] = mapped_column(Numeric(16, 2), default=0)
    status: Mapped[str] = mapped_column(String(40), default="quoted")
    opened_date: Mapped[date] = mapped_column(Date, default=date.today)
    due_date: Mapped[date | None] = mapped_column(Date)


class Vehicle(Base):
    __tablename__ = "vehicles"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"))
    registration: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    make_model: Mapped[str] = mapped_column(String(140), nullable=False)
    vehicle_type: Mapped[str] = mapped_column(String(60), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="active")
    odometer_km: Mapped[float] = mapped_column(Numeric(16, 1), default=0)


class FuelLog(Base):
    __tablename__ = "fuel_logs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    vehicle_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False)
    litres: Mapped[float] = mapped_column(Numeric(16, 3), nullable=False)
    price_per_litre: Mapped[float] = mapped_column(Numeric(16, 3), nullable=False)
    total_cost: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False)
    odometer_km: Mapped[float] = mapped_column(Numeric(16, 1), nullable=False)
    purpose: Mapped[str | None] = mapped_column(String(180))
    log_date: Mapped[date] = mapped_column(Date, default=date.today)


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    vehicle_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False)
    description: Mapped[str] = mapped_column(String(240), nullable=False)
    cost: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False)
    odometer_km: Mapped[float] = mapped_column(Numeric(16, 1), nullable=False)
    service_date: Mapped[date] = mapped_column(Date, default=date.today)


class Sale(Base):
    __tablename__ = "sales"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    branch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    customer_name: Mapped[str] = mapped_column(String(180), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(16, 4), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False)
    delivery_cost: Mapped[float] = mapped_column(Numeric(16, 2), default=0)
    total_amount: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(100))
    sale_date: Mapped[date] = mapped_column(Date, default=date.today)
