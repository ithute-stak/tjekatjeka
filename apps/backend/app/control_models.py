import uuid
from datetime import date, datetime
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()


class BrickRecipe(Base):
    __tablename__ = "brick_recipes"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    standard_output: Mapped[float] = mapped_column(Numeric(16, 4), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BrickRecipeInput(Base):
    __tablename__ = "brick_recipe_inputs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    recipe_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("brick_recipes.id", ondelete="CASCADE"), nullable=False)
    material_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("materials.id"), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(16, 4), nullable=False)


class AluminiumMeasurement(Base):
    __tablename__ = "aluminium_measurements"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("aluminium_jobs.id", ondelete="CASCADE"), nullable=False)
    item_name: Mapped[str] = mapped_column(String(160), nullable=False)
    width_mm: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    height_mm: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    area_m2: Mapped[float] = mapped_column(Numeric(16, 4), nullable=False)
    glass_type: Mapped[str | None] = mapped_column(String(120))
    notes: Mapped[str | None] = mapped_column(Text)


class DeliveryOrder(Base):
    __tablename__ = "delivery_orders"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    sale_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("sales.id"))
    branch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"))
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("vehicles.id"))
    delivery_no: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    customer_name: Mapped[str] = mapped_column(String(180), nullable=False)
    destination: Mapped[str] = mapped_column(String(240), nullable=False)
    load_description: Mapped[str] = mapped_column(String(240), nullable=False)
    quantity: Mapped[float | None] = mapped_column(Numeric(16, 4))
    unit: Mapped[str | None] = mapped_column(String(30))
    driver_name: Mapped[str | None] = mapped_column(String(140))
    delivery_fee: Mapped[float] = mapped_column(Numeric(16, 2), default=0)
    status: Mapped[str] = mapped_column(String(40), default="scheduled")
    scheduled_date: Mapped[date] = mapped_column(Date, default=date.today)
    delivered_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
