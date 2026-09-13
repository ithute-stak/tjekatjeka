import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .auth import current_claims
from .costing import production_total, unit_cost
from .db import get_db
from .models import (
    AluminiumJob,
    Branch,
    Expense,
    FuelLog,
    InventoryMovement,
    MaintenanceRecord,
    Material,
    Product,
    ProductionBatch,
    ProductionInput,
    Purchase,
    Sale,
    Vehicle,
)
from .schemas import (
    AluminiumJobCreate,
    ExpenseCreate,
    FuelLogCreate,
    MaintenanceCreate,
    MaterialCreate,
    ProductionBatchCreate,
    PurchaseCreate,
    SaleCreate,
    StockAdjustment,
    VehicleCreate,
)

router = APIRouter(prefix="/api/v1", dependencies=[Depends(current_claims)])


def row(model) -> dict:
    return {column.name: getattr(model, column.name) for column in model.__table__.columns}


@router.get("/branches")
def list_branches(db: Session = Depends(get_db)) -> list[dict]:
    return [row(item) for item in db.scalars(select(Branch).order_by(Branch.name)).all()]


@router.get("/materials")
def list_materials(db: Session = Depends(get_db)) -> list[dict]:
    return [row(item) for item in db.scalars(select(Material).order_by(Material.name)).all()]


@router.post("/materials", status_code=status.HTTP_201_CREATED)
def create_material(payload: MaterialCreate, db: Session = Depends(get_db)) -> dict:
    material = Material(**payload.model_dump())
    db.add(material)
    db.commit()
    db.refresh(material)
    return row(material)


@router.post("/materials/{material_id}/adjust")
def adjust_material(material_id: uuid.UUID, payload: StockAdjustment, db: Session = Depends(get_db)) -> dict:
    material = db.get(Material, material_id)
    if material is None:
        raise HTTPException(status_code=404, detail="Material not found")
    new_quantity = float(material.quantity_on_hand) + payload.quantity_delta
    if new_quantity < 0:
        raise HTTPException(status_code=409, detail="Adjustment would create negative stock")
    material.quantity_on_hand = new_quantity
    db.add(InventoryMovement(material_id=material.id, movement_type="adjustment", quantity_delta=payload.quantity_delta, reference=payload.reference, notes=payload.notes))
    db.commit()
    db.refresh(material)
    return row(material)


@router.get("/products")
def list_products(db: Session = Depends(get_db)) -> list[dict]:
    return [row(item) for item in db.scalars(select(Product).order_by(Product.name)).all()]


@router.get("/purchases")
def list_purchases(db: Session = Depends(get_db)) -> list[dict]:
    return [row(item) for item in db.scalars(select(Purchase).order_by(Purchase.purchase_date.desc()).limit(100)).all()]


@router.post("/purchases", status_code=status.HTTP_201_CREATED)
def create_purchase(payload: PurchaseCreate, db: Session = Depends(get_db)) -> dict:
    total = payload.quantity * payload.unit_cost
    purchase = Purchase(**payload.model_dump(), total_cost=total)
    db.add(purchase)
    if payload.material_id:
        material = db.get(Material, payload.material_id)
        if material is None:
            raise HTTPException(status_code=404, detail="Material not found")
        old_qty = float(material.quantity_on_hand)
        old_cost = float(material.average_unit_cost)
        new_qty = old_qty + payload.quantity
        material.average_unit_cost = ((old_qty * old_cost) + total) / new_qty if new_qty else payload.unit_cost
        material.quantity_on_hand = new_qty
        db.add(InventoryMovement(material_id=material.id, movement_type="purchase", quantity_delta=payload.quantity, reference=payload.reference, notes=f"Purchase from {payload.supplier_name}"))
    db.commit()
    db.refresh(purchase)
    return row(purchase)


@router.get("/expenses")
def list_expenses(db: Session = Depends(get_db)) -> list[dict]:
    return [row(item) for item in db.scalars(select(Expense).order_by(Expense.expense_date.desc()).limit(100)).all()]


@router.post("/expenses", status_code=status.HTTP_201_CREATED)
def create_expense(payload: ExpenseCreate, db: Session = Depends(get_db)) -> dict:
    expense = Expense(**payload.model_dump())
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return row(expense)


@router.get("/production")
def list_production(db: Session = Depends(get_db)) -> list[dict]:
    return [row(item) for item in db.scalars(select(ProductionBatch).order_by(ProductionBatch.production_date.desc()).limit(100)).all()]


@router.post("/production", status_code=status.HTTP_201_CREATED)
def create_production(payload: ProductionBatchCreate, db: Session = Depends(get_db)) -> dict:
    product = db.get(Product, payload.product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Finished product not found")
    if product.branch_id != payload.branch_id:
        raise HTTPException(status_code=409, detail="Product does not belong to selected branch")
    good_quantity = payload.produced_quantity - payload.rejected_quantity
    if good_quantity <= 0:
        raise HTTPException(status_code=422, detail="Good production quantity must be greater than zero")

    material_total = 0.0
    resolved_inputs: list[tuple[Material, float, float]] = []
    for item in payload.inputs:
        material = db.get(Material, item.material_id)
        if material is None:
            raise HTTPException(status_code=404, detail=f"Material {item.material_id} not found")
        if float(material.quantity_on_hand) < item.quantity:
            raise HTTPException(status_code=409, detail=f"Insufficient stock for {material.name}")
        cost = item.quantity * float(material.average_unit_cost)
        material_total += cost
        resolved_inputs.append((material, item.quantity, cost))

    total = production_total(material_total, payload.electricity_cost, payload.water_cost, payload.labour_cost, payload.machine_cost, payload.fuel_cost, payload.other_cost)
    per_good = unit_cost(total, payload.produced_quantity, payload.rejected_quantity)
    batch = ProductionBatch(
        branch_id=payload.branch_id,
        product_id=payload.product_id,
        batch_no=payload.batch_no,
        produced_quantity=payload.produced_quantity,
        rejected_quantity=payload.rejected_quantity,
        good_quantity=good_quantity,
        material_cost=material_total,
        electricity_cost=payload.electricity_cost,
        water_cost=payload.water_cost,
        labour_cost=payload.labour_cost,
        machine_cost=payload.machine_cost,
        fuel_cost=payload.fuel_cost,
        other_cost=payload.other_cost,
        total_cost=float(total),
        cost_per_good_unit=float(per_good),
        notes=payload.notes,
        production_date=payload.production_date,
    )
    db.add(batch)
    db.flush()
    for material, quantity, cost in resolved_inputs:
        unit_material_cost = float(material.average_unit_cost)
        material.quantity_on_hand = float(material.quantity_on_hand) - quantity
        db.add(ProductionInput(batch_id=batch.id, material_id=material.id, quantity=quantity, unit_cost=unit_material_cost, total_cost=cost))
        db.add(InventoryMovement(material_id=material.id, movement_type="production", quantity_delta=-quantity, reference=batch.batch_no, notes=f"Consumed in {batch.batch_no}"))
    product.quantity_on_hand = float(product.quantity_on_hand) + good_quantity
    db.commit()
    db.refresh(batch)
    return row(batch)


@router.get("/aluminium-jobs")
def list_aluminium_jobs(db: Session = Depends(get_db)) -> list[dict]:
    result = []
    for job in db.scalars(select(AluminiumJob).order_by(AluminiumJob.opened_date.desc()).limit(100)).all():
        data = row(job)
        total_cost = float(job.material_cost) + float(job.labour_cost) + float(job.transport_cost) + float(job.other_cost)
        data["total_cost"] = total_cost
        data["profit"] = float(job.quote_amount) - total_cost
        result.append(data)
    return result


@router.post("/aluminium-jobs", status_code=status.HTTP_201_CREATED)
def create_aluminium_job(payload: AluminiumJobCreate, db: Session = Depends(get_db)) -> dict:
    job = AluminiumJob(**payload.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)
    data = row(job)
    total_cost = float(job.material_cost) + float(job.labour_cost) + float(job.transport_cost) + float(job.other_cost)
    data["total_cost"] = total_cost
    data["profit"] = float(job.quote_amount) - total_cost
    return data


@router.get("/vehicles")
def list_vehicles(db: Session = Depends(get_db)) -> list[dict]:
    return [row(item) for item in db.scalars(select(Vehicle).order_by(Vehicle.registration)).all()]


@router.post("/vehicles", status_code=status.HTTP_201_CREATED)
def create_vehicle(payload: VehicleCreate, db: Session = Depends(get_db)) -> dict:
    vehicle = Vehicle(**payload.model_dump())
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return row(vehicle)


@router.get("/fuel")
def list_fuel(db: Session = Depends(get_db)) -> list[dict]:
    return [row(item) for item in db.scalars(select(FuelLog).order_by(FuelLog.log_date.desc()).limit(100)).all()]


@router.post("/fuel", status_code=status.HTTP_201_CREATED)
def create_fuel(payload: FuelLogCreate, db: Session = Depends(get_db)) -> dict:
    vehicle = db.get(Vehicle, payload.vehicle_id)
    if vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    if payload.odometer_km < float(vehicle.odometer_km):
        raise HTTPException(status_code=409, detail="Odometer cannot move backwards")
    log = FuelLog(**payload.model_dump(), total_cost=payload.litres * payload.price_per_litre)
    vehicle.odometer_km = payload.odometer_km
    db.add(log)
    db.commit()
    db.refresh(log)
    return row(log)


@router.get("/maintenance")
def list_maintenance(db: Session = Depends(get_db)) -> list[dict]:
    return [row(item) for item in db.scalars(select(MaintenanceRecord).order_by(MaintenanceRecord.service_date.desc()).limit(100)).all()]


@router.post("/maintenance", status_code=status.HTTP_201_CREATED)
def create_maintenance(payload: MaintenanceCreate, db: Session = Depends(get_db)) -> dict:
    vehicle = db.get(Vehicle, payload.vehicle_id)
    if vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    record = MaintenanceRecord(**payload.model_dump())
    vehicle.odometer_km = max(float(vehicle.odometer_km), payload.odometer_km)
    db.add(record)
    db.commit()
    db.refresh(record)
    return row(record)


@router.get("/sales")
def list_sales(db: Session = Depends(get_db)) -> list[dict]:
    return [row(item) for item in db.scalars(select(Sale).order_by(Sale.sale_date.desc()).limit(100)).all()]


@router.post("/sales", status_code=status.HTTP_201_CREATED)
def create_sale(payload: SaleCreate, db: Session = Depends(get_db)) -> dict:
    product = db.get(Product, payload.product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.branch_id != payload.branch_id:
        raise HTTPException(status_code=409, detail="Product does not belong to selected branch")
    if float(product.quantity_on_hand) < payload.quantity:
        raise HTTPException(status_code=409, detail="Insufficient finished stock")
    product.quantity_on_hand = float(product.quantity_on_hand) - payload.quantity
    sale = Sale(**payload.model_dump(), total_amount=(payload.quantity * payload.unit_price) + payload.delivery_cost)
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return row(sale)


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)) -> dict:
    today = date.today()
    month_start = today.replace(day=1)
    sales = float(db.scalar(select(func.coalesce(func.sum(Sale.total_amount), 0)).where(Sale.sale_date >= month_start)) or 0)
    expenses = float(db.scalar(select(func.coalesce(func.sum(Expense.amount), 0)).where(Expense.expense_date >= month_start)) or 0)
    purchases = float(db.scalar(select(func.coalesce(func.sum(Purchase.total_cost), 0)).where(Purchase.purchase_date >= month_start)) or 0)
    fuel = float(db.scalar(select(func.coalesce(func.sum(FuelLog.total_cost), 0)).where(FuelLog.log_date >= month_start)) or 0)
    maintenance = float(db.scalar(select(func.coalesce(func.sum(MaintenanceRecord.cost), 0)).where(MaintenanceRecord.service_date >= month_start)) or 0)
    production_units = float(db.scalar(select(func.coalesce(func.sum(ProductionBatch.good_quantity), 0)).where(ProductionBatch.production_date >= month_start)) or 0)
    active_jobs = int(db.scalar(select(func.count()).select_from(AluminiumJob).where(AluminiumJob.status.notin_(["completed", "cancelled"]))) or 0)
    active_vehicles = int(db.scalar(select(func.count()).select_from(Vehicle).where(Vehicle.status == "active")) or 0)

    low_stock = [
        {"id": material.id, "name": material.name, "quantity_on_hand": float(material.quantity_on_hand), "unit": material.unit, "reorder_level": float(material.reorder_level)}
        for material in db.scalars(select(Material).order_by(Material.name)).all()
        if float(material.quantity_on_hand) <= float(material.reorder_level)
    ]
    products = [
        {"id": item.id, "name": item.name, "quantity_on_hand": float(item.quantity_on_hand), "unit": item.unit, "selling_price": float(item.selling_price)}
        for item in db.scalars(select(Product).order_by(Product.name)).all()
    ]
    branch_summaries = []
    for branch in db.scalars(select(Branch).order_by(Branch.name)).all():
        branch_sales = float(db.scalar(select(func.coalesce(func.sum(Sale.total_amount), 0)).where(Sale.branch_id == branch.id, Sale.sale_date >= month_start)) or 0)
        branch_expenses = float(db.scalar(select(func.coalesce(func.sum(Expense.amount), 0)).where(Expense.branch_id == branch.id, Expense.expense_date >= month_start)) or 0)
        branch_purchases = float(db.scalar(select(func.coalesce(func.sum(Purchase.total_cost), 0)).where(Purchase.branch_id == branch.id, Purchase.purchase_date >= month_start)) or 0)
        branch_summaries.append({"id": branch.id, "code": branch.code, "name": branch.name, "division": branch.division, "sales": branch_sales, "expenses": branch_expenses, "purchases": branch_purchases})

    operating_spend = expenses + purchases + fuel + maintenance
    return {
        "period": month_start.isoformat(),
        "sales": sales,
        "expenses": expenses,
        "purchases": purchases,
        "fuel": fuel,
        "maintenance": maintenance,
        "operating_spend": operating_spend,
        "cash_margin_proxy": sales - operating_spend,
        "production_units": production_units,
        "active_aluminium_jobs": active_jobs,
        "active_vehicles": active_vehicles,
        "low_stock": low_stock,
        "finished_stock": products,
        "branches": branch_summaries,
    }
