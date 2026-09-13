import uuid
from datetime import date
from pydantic import BaseModel, Field


class CustomerCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    phone: str | None = None
    email: str | None = None


class SupplierCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    phone: str | None = None
    email: str | None = None


class CustomerInvoiceCreate(BaseModel):
    customer_id: uuid.UUID
    branch_id: uuid.UUID | None = None
    invoice_no: str
    description: str
    amount: float = Field(gt=0)
    invoice_date: date = Field(default_factory=date.today)
    due_date: date | None = None


class CustomerPaymentCreate(BaseModel):
    customer_id: uuid.UUID
    invoice_id: uuid.UUID | None = None
    amount: float = Field(gt=0)
    method: str = "bank"
    reference: str | None = None
    payment_date: date = Field(default_factory=date.today)
    notes: str | None = None


class SupplierBillCreate(BaseModel):
    supplier_id: uuid.UUID
    branch_id: uuid.UUID | None = None
    bill_no: str
    description: str
    amount: float = Field(gt=0)
    bill_date: date = Field(default_factory=date.today)
    due_date: date | None = None


class SupplierPaymentCreate(BaseModel):
    supplier_id: uuid.UUID
    bill_id: uuid.UUID | None = None
    amount: float = Field(gt=0)
    method: str = "bank"
    reference: str | None = None
    payment_date: date = Field(default_factory=date.today)
    notes: str | None = None


class RecipeInputCreate(BaseModel):
    material_id: uuid.UUID
    quantity: float = Field(gt=0)


class BrickRecipeCreate(BaseModel):
    product_id: uuid.UUID
    name: str
    standard_output: float = Field(gt=0)
    notes: str | None = None
    inputs: list[RecipeInputCreate] = Field(min_length=1)


class AluminiumMeasurementCreate(BaseModel):
    job_id: uuid.UUID
    item_name: str
    width_mm: float = Field(gt=0)
    height_mm: float = Field(gt=0)
    quantity: float = Field(gt=0)
    glass_type: str | None = None
    notes: str | None = None


class DeliveryCreate(BaseModel):
    sale_id: uuid.UUID | None = None
    branch_id: uuid.UUID | None = None
    vehicle_id: uuid.UUID | None = None
    delivery_no: str
    customer_name: str
    destination: str
    load_description: str
    quantity: float | None = Field(default=None, gt=0)
    unit: str | None = None
    driver_name: str | None = None
    delivery_fee: float = Field(default=0, ge=0)
    status: str = "scheduled"
    scheduled_date: date = Field(default_factory=date.today)
    notes: str | None = None


class DeliveryStatusUpdate(BaseModel):
    status: str
    delivered_date: date | None = None
    vehicle_id: uuid.UUID | None = None
    driver_name: str | None = None
