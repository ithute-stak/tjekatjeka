import uuid
from datetime import date

from pydantic import BaseModel, Field


class MaterialCreate(BaseModel):
    branch_id: uuid.UUID | None = None
    code: str = Field(min_length=2, max_length=40)
    name: str = Field(min_length=2, max_length=140)
    category: str = Field(min_length=2, max_length=60)
    unit: str = Field(min_length=1, max_length=30)
    reorder_level: float = Field(default=0, ge=0)


class StockAdjustment(BaseModel):
    quantity_delta: float
    reference: str | None = None
    notes: str | None = None


class PurchaseCreate(BaseModel):
    branch_id: uuid.UUID | None = None
    material_id: uuid.UUID | None = None
    supplier_name: str
    item_name: str
    category: str
    quantity: float = Field(gt=0)
    unit: str
    unit_cost: float = Field(ge=0)
    reference: str | None = None
    purchase_date: date = Field(default_factory=date.today)


class ExpenseCreate(BaseModel):
    branch_id: uuid.UUID | None = None
    category: str
    description: str
    amount: float = Field(gt=0)
    reference: str | None = None
    expense_date: date = Field(default_factory=date.today)


class ProductionInputCreate(BaseModel):
    material_id: uuid.UUID
    quantity: float = Field(gt=0)


class ProductionBatchCreate(BaseModel):
    branch_id: uuid.UUID
    product_id: uuid.UUID
    batch_no: str
    produced_quantity: float = Field(gt=0)
    rejected_quantity: float = Field(default=0, ge=0)
    electricity_cost: float = Field(default=0, ge=0)
    water_cost: float = Field(default=0, ge=0)
    labour_cost: float = Field(default=0, ge=0)
    machine_cost: float = Field(default=0, ge=0)
    fuel_cost: float = Field(default=0, ge=0)
    other_cost: float = Field(default=0, ge=0)
    notes: str | None = None
    production_date: date = Field(default_factory=date.today)
    inputs: list[ProductionInputCreate] = Field(min_length=1)


class AluminiumJobCreate(BaseModel):
    branch_id: uuid.UUID
    job_no: str
    customer_name: str
    description: str
    quote_amount: float = Field(default=0, ge=0)
    material_cost: float = Field(default=0, ge=0)
    labour_cost: float = Field(default=0, ge=0)
    transport_cost: float = Field(default=0, ge=0)
    other_cost: float = Field(default=0, ge=0)
    status: str = "quoted"
    opened_date: date = Field(default_factory=date.today)
    due_date: date | None = None


class VehicleCreate(BaseModel):
    branch_id: uuid.UUID | None = None
    registration: str
    make_model: str
    vehicle_type: str
    status: str = "active"
    odometer_km: float = Field(default=0, ge=0)


class FuelLogCreate(BaseModel):
    vehicle_id: uuid.UUID
    litres: float = Field(gt=0)
    price_per_litre: float = Field(gt=0)
    odometer_km: float = Field(ge=0)
    purpose: str | None = None
    log_date: date = Field(default_factory=date.today)


class MaintenanceCreate(BaseModel):
    vehicle_id: uuid.UUID
    description: str
    cost: float = Field(gt=0)
    odometer_km: float = Field(ge=0)
    service_date: date = Field(default_factory=date.today)


class SaleCreate(BaseModel):
    branch_id: uuid.UUID
    product_id: uuid.UUID
    customer_name: str
    quantity: float = Field(gt=0)
    unit_price: float = Field(gt=0)
    delivery_cost: float = Field(default=0, ge=0)
    reference: str | None = None
    sale_date: date = Field(default_factory=date.today)
