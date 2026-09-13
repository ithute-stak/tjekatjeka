import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .accounting_models import CustomerInvoice, CustomerPayment, SupplierBill, SupplierPayment
from .advanced_schemas import (
    AluminiumMeasurementCreate,
    BrickRecipeCreate,
    CustomerCreate,
    CustomerInvoiceCreate,
    CustomerPaymentCreate,
    DeliveryCreate,
    DeliveryStatusUpdate,
    SupplierBillCreate,
    SupplierCreate,
    SupplierPaymentCreate,
)
from .auth import current_claims
from .control_models import AluminiumMeasurement, BrickRecipe, BrickRecipeInput, DeliveryOrder
from .db import get_db
from .models import (
    AluminiumJob,
    Customer,
    Material,
    Product,
    ProductionBatch,
    ProductionInput,
    Supplier,
    Vehicle,
)

router = APIRouter(prefix="/api/v1", dependencies=[Depends(current_claims)])


def row(model) -> dict:
    return {column.name: getattr(model, column.name) for column in model.__table__.columns}


def customer_invoice_row(item: CustomerInvoice, db: Session) -> dict:
    data = row(item)
    paid = float(db.scalar(select(func.coalesce(func.sum(CustomerPayment.amount), 0)).where(CustomerPayment.invoice_id == item.id)) or 0)
    data["paid_amount"] = paid
    data["balance"] = max(float(item.amount) - paid, 0)
    return data


def supplier_bill_row(item: SupplierBill, db: Session) -> dict:
    data = row(item)
    paid = float(db.scalar(select(func.coalesce(func.sum(SupplierPayment.amount), 0)).where(SupplierPayment.bill_id == item.id)) or 0)
    data["paid_amount"] = paid
    data["balance"] = max(float(item.amount) - paid, 0)
    return data


def refresh_invoice_status(invoice: CustomerInvoice, db: Session) -> None:
    paid = float(db.scalar(select(func.coalesce(func.sum(CustomerPayment.amount), 0)).where(CustomerPayment.invoice_id == invoice.id)) or 0)
    invoice.status = "paid" if paid >= float(invoice.amount) else ("partial" if paid > 0 else "open")


def refresh_bill_status(bill: SupplierBill, db: Session) -> None:
    paid = float(db.scalar(select(func.coalesce(func.sum(SupplierPayment.amount), 0)).where(SupplierPayment.bill_id == bill.id)) or 0)
    bill.status = "paid" if paid >= float(bill.amount) else ("partial" if paid > 0 else "open")


@router.get("/customers")
def customers(db: Session = Depends(get_db)) -> list[dict]:
    result = []
    for customer in db.scalars(select(Customer).order_by(Customer.name)).all():
        data = row(customer)
        invoiced = float(db.scalar(select(func.coalesce(func.sum(CustomerInvoice.amount), 0)).where(CustomerInvoice.customer_id == customer.id)) or 0)
        paid = float(db.scalar(select(func.coalesce(func.sum(CustomerPayment.amount), 0)).where(CustomerPayment.customer_id == customer.id)) or 0)
        data.update(invoiced=invoiced, paid=paid, balance=invoiced - paid)
        result.append(data)
    return result


@router.post("/customers", status_code=status.HTTP_201_CREATED)
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)) -> dict:
    customer = Customer(**payload.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return row(customer)


@router.get("/suppliers")
def suppliers(db: Session = Depends(get_db)) -> list[dict]:
    result = []
    for supplier in db.scalars(select(Supplier).order_by(Supplier.name)).all():
        data = row(supplier)
        billed = float(db.scalar(select(func.coalesce(func.sum(SupplierBill.amount), 0)).where(SupplierBill.supplier_id == supplier.id)) or 0)
        paid = float(db.scalar(select(func.coalesce(func.sum(SupplierPayment.amount), 0)).where(SupplierPayment.supplier_id == supplier.id)) or 0)
        data.update(billed=billed, paid=paid, balance=billed - paid)
        result.append(data)
    return result


@router.post("/suppliers", status_code=status.HTTP_201_CREATED)
def create_supplier(payload: SupplierCreate, db: Session = Depends(get_db)) -> dict:
    if db.scalar(select(Supplier).where(func.lower(Supplier.name) == payload.name.lower())):
        raise HTTPException(status_code=409, detail="Supplier already exists")
    supplier = Supplier(**payload.model_dump())
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return row(supplier)


@router.get("/customer-invoices")
def customer_invoices(db: Session = Depends(get_db)) -> list[dict]:
    return [customer_invoice_row(item, db) for item in db.scalars(select(CustomerInvoice).order_by(CustomerInvoice.invoice_date.desc())).all()]


@router.post("/customer-invoices", status_code=status.HTTP_201_CREATED)
def create_customer_invoice(payload: CustomerInvoiceCreate, db: Session = Depends(get_db)) -> dict:
    if db.get(Customer, payload.customer_id) is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    invoice = CustomerInvoice(**payload.model_dump())
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return customer_invoice_row(invoice, db)


@router.get("/customer-payments")
def customer_payments(db: Session = Depends(get_db)) -> list[dict]:
    return [row(item) for item in db.scalars(select(CustomerPayment).order_by(CustomerPayment.payment_date.desc())).all()]


@router.post("/customer-payments", status_code=status.HTTP_201_CREATED)
def create_customer_payment(payload: CustomerPaymentCreate, db: Session = Depends(get_db)) -> dict:
    if db.get(Customer, payload.customer_id) is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    invoice = db.get(CustomerInvoice, payload.invoice_id) if payload.invoice_id else None
    if payload.invoice_id and invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice and invoice.customer_id != payload.customer_id:
        raise HTTPException(status_code=409, detail="Invoice belongs to another customer")
    payment = CustomerPayment(**payload.model_dump())
    db.add(payment)
    db.flush()
    if invoice:
        refresh_invoice_status(invoice, db)
    db.commit()
    db.refresh(payment)
    return row(payment)


@router.get("/customers/{customer_id}/ledger")
def customer_ledger(customer_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    invoices = db.scalars(select(CustomerInvoice).where(CustomerInvoice.customer_id == customer_id).order_by(CustomerInvoice.invoice_date.desc())).all()
    payments = db.scalars(select(CustomerPayment).where(CustomerPayment.customer_id == customer_id).order_by(CustomerPayment.payment_date.desc())).all()
    invoiced = sum(float(item.amount) for item in invoices)
    paid = sum(float(item.amount) for item in payments)
    return {"customer": row(customer), "invoiced": invoiced, "paid": paid, "balance": invoiced - paid, "invoices": [customer_invoice_row(item, db) for item in invoices], "payments": [row(item) for item in payments]}


@router.get("/supplier-bills")
def supplier_bills(db: Session = Depends(get_db)) -> list[dict]:
    return [supplier_bill_row(item, db) for item in db.scalars(select(SupplierBill).order_by(SupplierBill.bill_date.desc())).all()]


@router.post("/supplier-bills", status_code=status.HTTP_201_CREATED)
def create_supplier_bill(payload: SupplierBillCreate, db: Session = Depends(get_db)) -> dict:
    if db.get(Supplier, payload.supplier_id) is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    bill = SupplierBill(**payload.model_dump())
    db.add(bill)
    db.commit()
    db.refresh(bill)
    return supplier_bill_row(bill, db)


@router.get("/supplier-payments")
def supplier_payments(db: Session = Depends(get_db)) -> list[dict]:
    return [row(item) for item in db.scalars(select(SupplierPayment).order_by(SupplierPayment.payment_date.desc())).all()]


@router.post("/supplier-payments", status_code=status.HTTP_201_CREATED)
def create_supplier_payment(payload: SupplierPaymentCreate, db: Session = Depends(get_db)) -> dict:
    if db.get(Supplier, payload.supplier_id) is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    bill = db.get(SupplierBill, payload.bill_id) if payload.bill_id else None
    if payload.bill_id and bill is None:
        raise HTTPException(status_code=404, detail="Supplier bill not found")
    if bill and bill.supplier_id != payload.supplier_id:
        raise HTTPException(status_code=409, detail="Bill belongs to another supplier")
    payment = SupplierPayment(**payload.model_dump())
    db.add(payment)
    db.flush()
    if bill:
        refresh_bill_status(bill, db)
    db.commit()
    db.refresh(payment)
    return row(payment)


@router.get("/suppliers/{supplier_id}/ledger")
def supplier_ledger(supplier_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    supplier = db.get(Supplier, supplier_id)
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    bills = db.scalars(select(SupplierBill).where(SupplierBill.supplier_id == supplier_id).order_by(SupplierBill.bill_date.desc())).all()
    payments = db.scalars(select(SupplierPayment).where(SupplierPayment.supplier_id == supplier_id).order_by(SupplierPayment.payment_date.desc())).all()
    billed = sum(float(item.amount) for item in bills)
    paid = sum(float(item.amount) for item in payments)
    return {"supplier": row(supplier), "billed": billed, "paid": paid, "balance": billed - paid, "bills": [supplier_bill_row(item, db) for item in bills], "payments": [row(item) for item in payments]}


@router.get("/brick-recipes")
def brick_recipes(db: Session = Depends(get_db)) -> list[dict]:
    result = []
    for recipe in db.scalars(select(BrickRecipe).order_by(BrickRecipe.name)).all():
        data = row(recipe)
        data["inputs"] = [row(item) for item in db.scalars(select(BrickRecipeInput).where(BrickRecipeInput.recipe_id == recipe.id)).all()]
        result.append(data)
    return result


@router.post("/brick-recipes", status_code=status.HTTP_201_CREATED)
def create_brick_recipe(payload: BrickRecipeCreate, db: Session = Depends(get_db)) -> dict:
    if db.get(Product, payload.product_id) is None:
        raise HTTPException(status_code=404, detail="Product not found")
    for item in payload.inputs:
        if db.get(Material, item.material_id) is None:
            raise HTTPException(status_code=404, detail=f"Material {item.material_id} not found")
    recipe = BrickRecipe(product_id=payload.product_id, name=payload.name, standard_output=payload.standard_output, notes=payload.notes)
    db.add(recipe)
    db.flush()
    for item in payload.inputs:
        db.add(BrickRecipeInput(recipe_id=recipe.id, material_id=item.material_id, quantity=item.quantity))
    db.commit()
    db.refresh(recipe)
    data = row(recipe)
    data["inputs"] = [row(item) for item in db.scalars(select(BrickRecipeInput).where(BrickRecipeInput.recipe_id == recipe.id)).all()]
    return data


@router.get("/production/{batch_id}/variance")
def production_variance(batch_id: uuid.UUID, recipe_id: uuid.UUID = Query(...), db: Session = Depends(get_db)) -> dict:
    batch = db.get(ProductionBatch, batch_id)
    recipe = db.get(BrickRecipe, recipe_id)
    if batch is None or recipe is None:
        raise HTTPException(status_code=404, detail="Batch or recipe not found")
    if batch.product_id != recipe.product_id:
        raise HTTPException(status_code=409, detail="Recipe is for a different finished product")
    scale = float(batch.good_quantity) / float(recipe.standard_output)
    expected = {item.material_id: float(item.quantity) * scale for item in db.scalars(select(BrickRecipeInput).where(BrickRecipeInput.recipe_id == recipe.id)).all()}
    actual = {item.material_id: float(item.quantity) for item in db.scalars(select(ProductionInput).where(ProductionInput.batch_id == batch.id)).all()}
    details = []
    for material_id in set(expected) | set(actual):
        material = db.get(Material, material_id)
        exp = expected.get(material_id, 0.0)
        act = actual.get(material_id, 0.0)
        variance = act - exp
        details.append({"material_id": material_id, "material_name": material.name if material else "Unknown", "unit": material.unit if material else "", "expected": exp, "actual": act, "variance": variance, "variance_pct": (variance / exp * 100) if exp else None, "cost_impact": variance * float(material.average_unit_cost) if material else 0})
    return {"batch_id": batch.id, "batch_no": batch.batch_no, "recipe_id": recipe.id, "recipe_name": recipe.name, "good_quantity": float(batch.good_quantity), "reject_rate_pct": (float(batch.rejected_quantity) / float(batch.produced_quantity) * 100) if float(batch.produced_quantity) else 0, "materials": details, "total_variance_cost": sum(item["cost_impact"] for item in details)}


@router.get("/aluminium-measurements")
def aluminium_measurements(job_id: uuid.UUID | None = None, db: Session = Depends(get_db)) -> list[dict]:
    query = select(AluminiumMeasurement)
    if job_id:
        query = query.where(AluminiumMeasurement.job_id == job_id)
    return [row(item) for item in db.scalars(query.order_by(AluminiumMeasurement.item_name)).all()]


@router.post("/aluminium-measurements", status_code=status.HTTP_201_CREATED)
def create_aluminium_measurement(payload: AluminiumMeasurementCreate, db: Session = Depends(get_db)) -> dict:
    if db.get(AluminiumJob, payload.job_id) is None:
        raise HTTPException(status_code=404, detail="Aluminium job not found")
    area = payload.width_mm * payload.height_mm * payload.quantity / 1_000_000
    measurement = AluminiumMeasurement(**payload.model_dump(), area_m2=area)
    db.add(measurement)
    db.commit()
    db.refresh(measurement)
    return row(measurement)


@router.get("/deliveries")
def deliveries(db: Session = Depends(get_db)) -> list[dict]:
    return [row(item) for item in db.scalars(select(DeliveryOrder).order_by(DeliveryOrder.scheduled_date.desc())).all()]


@router.post("/deliveries", status_code=status.HTTP_201_CREATED)
def create_delivery(payload: DeliveryCreate, db: Session = Depends(get_db)) -> dict:
    if payload.vehicle_id and db.get(Vehicle, payload.vehicle_id) is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    delivery = DeliveryOrder(**payload.model_dump())
    db.add(delivery)
    db.commit()
    db.refresh(delivery)
    return row(delivery)


@router.patch("/deliveries/{delivery_id}")
def update_delivery(delivery_id: uuid.UUID, payload: DeliveryStatusUpdate, db: Session = Depends(get_db)) -> dict:
    delivery = db.get(DeliveryOrder, delivery_id)
    if delivery is None:
        raise HTTPException(status_code=404, detail="Delivery not found")
    if payload.status not in {"scheduled", "loaded", "in_transit", "delivered", "cancelled"}:
        raise HTTPException(status_code=422, detail="Invalid delivery status")
    if payload.vehicle_id and db.get(Vehicle, payload.vehicle_id) is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    delivery.status = payload.status
    if payload.vehicle_id is not None:
        delivery.vehicle_id = payload.vehicle_id
    if payload.driver_name is not None:
        delivery.driver_name = payload.driver_name
    delivery.delivered_date = payload.delivered_date or (date.today() if payload.status == "delivered" else delivery.delivered_date)
    db.commit()
    db.refresh(delivery)
    return row(delivery)


@router.get("/management-summary")
def management_summary(db: Session = Depends(get_db)) -> dict:
    invoices = db.scalars(select(CustomerInvoice)).all()
    customer_payments_all = db.scalars(select(CustomerPayment)).all()
    bills = db.scalars(select(SupplierBill)).all()
    supplier_payments_all = db.scalars(select(SupplierPayment)).all()
    receivables = sum(float(item.amount) for item in invoices) - sum(float(item.amount) for item in customer_payments_all)
    payables = sum(float(item.amount) for item in bills) - sum(float(item.amount) for item in supplier_payments_all)
    pending_deliveries = int(db.scalar(select(func.count()).select_from(DeliveryOrder).where(DeliveryOrder.status.notin_(["delivered", "cancelled"]))) or 0)
    production = db.scalars(select(ProductionBatch)).all()
    produced = sum(float(item.produced_quantity) for item in production)
    rejected = sum(float(item.rejected_quantity) for item in production)
    total_production_cost = sum(float(item.total_cost) for item in production)
    good = sum(float(item.good_quantity) for item in production)
    measurement_area = float(db.scalar(select(func.coalesce(func.sum(AluminiumMeasurement.area_m2), 0))) or 0)
    return {"receivables": receivables, "payables": payables, "net_working_balance": receivables - payables, "pending_deliveries": pending_deliveries, "production_reject_rate_pct": (rejected / produced * 100) if produced else 0, "average_brick_cost": (total_production_cost / good) if good else 0, "aluminium_measured_area_m2": measurement_area, "active_recipes": int(db.scalar(select(func.count()).select_from(BrickRecipe).where(BrickRecipe.is_active.is_(True))) or 0)}
