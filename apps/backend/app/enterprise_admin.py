import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .authorization import ALLOWED_ROLES, current_profile, require_roles
from .config import settings
from .db import get_db
from .enterprise_admin_models import ApprovalRequest, AuditEvent, DocumentRecord, Employee, Notification, PayrollRun, Payslip
from .enterprise_schemas import ApprovalCreate, ApprovalDecision, EmployeeCreate, NotificationCreate, PayrollRunCreate, PayrollStatusUpdate, ProfileRoleUpdate
from .models import Profile

router = APIRouter(prefix="/api/v1", dependencies=[Depends(current_profile)])


def row(model) -> dict:
    return {column.name: getattr(model, column.name) for column in model.__table__.columns}


def audit(db: Session, profile: Profile, action: str, entity_type: str, entity_id: uuid.UUID | None, summary: str) -> None:
    db.add(AuditEvent(actor=profile.email_snapshot, action=action, entity_type=entity_type, entity_id=entity_id, summary=summary))


def notify_governance(db: Session, title: str, message: str, severity: str = "info") -> None:
    profiles = db.scalars(select(Profile).where(Profile.role.in_(["admin", "director"]))).all()
    for profile in profiles:
        if profile.email_snapshot:
            db.add(Notification(recipient=profile.email_snapshot, title=title, message=message, severity=severity))


@router.get("/employees")
def list_employees(db: Session = Depends(get_db)) -> list[dict]:
    return [row(item) for item in db.scalars(select(Employee).order_by(Employee.full_name)).all()]


@router.post("/employees", status_code=status.HTTP_201_CREATED)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db), profile: Profile = Depends(require_roles("admin", "director", "manager", "hr"))) -> dict:
    if db.scalar(select(Employee).where(Employee.employee_no == payload.employee_no)):
        raise HTTPException(status_code=409, detail="Employee number already exists")
    employee = Employee(**payload.model_dump())
    db.add(employee)
    db.flush()
    audit(db, profile, "create", "employee", employee.id, f"Created employee {employee.employee_no} {employee.full_name}")
    db.commit()
    db.refresh(employee)
    return row(employee)


@router.get("/payroll-runs")
def list_payroll_runs(db: Session = Depends(get_db)) -> list[dict]:
    result = []
    for run in db.scalars(select(PayrollRun).order_by(PayrollRun.pay_date.desc())).all():
        data = row(run)
        slips = [row(item) for item in db.scalars(select(Payslip).where(Payslip.payroll_run_id == run.id)).all()]
        data["payslips"] = slips
        result.append(data)
    return result


@router.post("/payroll-runs", status_code=status.HTTP_201_CREATED)
def create_payroll_run(payload: PayrollRunCreate, db: Session = Depends(get_db), profile: Profile = Depends(require_roles("admin", "director", "hr", "accountant"))) -> dict:
    if db.scalar(select(PayrollRun).where(PayrollRun.period_label == payload.period_label)):
        raise HTTPException(status_code=409, detail="Payroll period already exists")
    run = PayrollRun(period_label=payload.period_label, pay_date=payload.pay_date, status="draft")
    db.add(run)
    db.flush()
    gross_total = deduction_total = net_total = 0.0
    seen: set[uuid.UUID] = set()
    for item in payload.payslips:
        if item.employee_id in seen:
            raise HTTPException(status_code=422, detail="Employee appears more than once in payroll")
        seen.add(item.employee_id)
        employee = db.get(Employee, item.employee_id)
        if employee is None or not employee.active:
            raise HTTPException(status_code=404, detail=f"Active employee {item.employee_id} not found")
        basic = float(employee.basic_salary)
        gross = basic + item.allowances
        net = gross - item.deductions
        if net < 0:
            raise HTTPException(status_code=422, detail=f"Deductions exceed gross pay for {employee.full_name}")
        db.add(Payslip(payroll_run_id=run.id, employee_id=employee.id, basic_salary=basic, allowances=item.allowances, deductions=item.deductions, net_pay=net, notes=item.notes))
        gross_total += gross
        deduction_total += item.deductions
        net_total += net
    run.gross_total = gross_total
    run.deduction_total = deduction_total
    run.net_total = net_total
    approval = ApprovalRequest(entity_type="payroll_run", entity_id=run.id, title=f"Approve payroll {run.period_label}", amount=net_total, requested_by=profile.email_snapshot)
    db.add(approval)
    audit(db, profile, "create", "payroll_run", run.id, f"Prepared payroll {run.period_label} net M{net_total:.2f}")
    notify_governance(db, "Payroll approval required", f"Payroll {run.period_label} for M{net_total:.2f} is waiting for approval", "warning")
    db.commit()
    db.refresh(run)
    data = row(run)
    data["approval_id"] = approval.id
    return data


@router.patch("/payroll-runs/{run_id}")
def update_payroll_status(run_id: uuid.UUID, payload: PayrollStatusUpdate, db: Session = Depends(get_db), profile: Profile = Depends(require_roles("admin", "director", "accountant"))) -> dict:
    run = db.get(PayrollRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Payroll run not found")
    if payload.status not in {"approved", "paid", "cancelled"}:
        raise HTTPException(status_code=422, detail="Invalid payroll status")
    if payload.status in {"approved", "paid"}:
        approval = db.scalar(select(ApprovalRequest).where(ApprovalRequest.entity_type == "payroll_run", ApprovalRequest.entity_id == run.id, ApprovalRequest.status == "approved"))
        if approval is None:
            raise HTTPException(status_code=409, detail="Payroll must have an approved governance request first")
    run.status = payload.status
    audit(db, profile, "status", "payroll_run", run.id, f"Payroll {run.period_label} changed to {payload.status}")
    db.commit()
    db.refresh(run)
    return row(run)


@router.get("/approvals")
def list_approvals(db: Session = Depends(get_db)) -> list[dict]:
    return [row(item) for item in db.scalars(select(ApprovalRequest).order_by(ApprovalRequest.created_at.desc())).all()]


@router.post("/approvals", status_code=status.HTTP_201_CREATED)
def create_approval(payload: ApprovalCreate, db: Session = Depends(get_db), profile: Profile = Depends(current_profile)) -> dict:
    item = ApprovalRequest(**payload.model_dump(), requested_by=profile.email_snapshot)
    db.add(item)
    db.flush()
    audit(db, profile, "request", "approval", item.id, f"Requested approval: {item.title}")
    notify_governance(db, "Approval required", item.title, "warning")
    db.commit()
    db.refresh(item)
    return row(item)


@router.patch("/approvals/{approval_id}")
def decide_approval(approval_id: uuid.UUID, payload: ApprovalDecision, db: Session = Depends(get_db), profile: Profile = Depends(require_roles("admin", "director"))) -> dict:
    item = db.get(ApprovalRequest, approval_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Approval request not found")
    if item.status != "pending":
        raise HTTPException(status_code=409, detail="Approval has already been decided")
    if payload.status not in {"approved", "rejected"}:
        raise HTTPException(status_code=422, detail="Decision must be approved or rejected")
    item.status = payload.status
    item.decision_note = payload.decision_note
    item.decided_by = profile.email_snapshot
    item.decided_at = datetime.now(timezone.utc)
    audit(db, profile, "decision", "approval", item.id, f"{payload.status.title()}: {item.title}")
    db.commit()
    db.refresh(item)
    return row(item)


@router.get("/documents")
def list_documents(entity_type: str | None = None, entity_id: uuid.UUID | None = None, db: Session = Depends(get_db)) -> list[dict]:
    query = select(DocumentRecord)
    if entity_type:
        query = query.where(DocumentRecord.entity_type == entity_type)
    if entity_id:
        query = query.where(DocumentRecord.entity_id == entity_id)
    return [row(item) for item in db.scalars(query.order_by(DocumentRecord.created_at.desc())).all()]


@router.post("/documents/upload", status_code=status.HTTP_201_CREATED)
def upload_document(
    entity_type: str = Form(...),
    title: str = Form(...),
    document_type: str = Form(...),
    entity_id: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    profile: Profile = Depends(require_roles("admin", "director", "manager", "accountant", "hr", "brick_manager", "aluminium_manager", "fleet_manager", "storekeeper", "sales")),
) -> dict:
    storage = Path(settings.document_storage_path)
    storage.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "document").suffix[:12]
    key = f"{uuid.uuid4().hex}{suffix}"
    target = storage / key
    content = file.file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Document exceeds 20 MB limit")
    target.write_bytes(content)
    parsed_entity_id = uuid.UUID(entity_id) if entity_id else None
    item = DocumentRecord(entity_type=entity_type, entity_id=parsed_entity_id, title=title, document_type=document_type, storage_url=f"local:{key}", uploaded_by=profile.email_snapshot)
    db.add(item)
    db.flush()
    audit(db, profile, "upload", "document", item.id, f"Uploaded {title}")
    db.commit()
    db.refresh(item)
    return row(item)


@router.get("/documents/{document_id}/download")
def download_document(document_id: uuid.UUID, db: Session = Depends(get_db)):
    item = db.get(DocumentRecord, document_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if not item.storage_url.startswith("local:"):
        raise HTTPException(status_code=409, detail="Document is stored externally")
    key = item.storage_url.removeprefix("local:")
    target = Path(settings.document_storage_path) / key
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="Document file is missing")
    return FileResponse(target, filename=item.title)


@router.get("/audit-events")
def list_audit_events(db: Session = Depends(get_db), _: Profile = Depends(require_roles("admin", "director", "manager", "accountant"))) -> list[dict]:
    return [row(item) for item in db.scalars(select(AuditEvent).order_by(AuditEvent.occurred_at.desc()).limit(500)).all()]


@router.get("/notifications")
def list_notifications(db: Session = Depends(get_db), profile: Profile = Depends(current_profile)) -> list[dict]:
    query = select(Notification)
    if profile.role not in {"admin", "director"}:
        query = query.where(Notification.recipient == (profile.email_snapshot or ""))
    return [row(item) for item in db.scalars(query.order_by(Notification.created_at.desc()).limit(200)).all()]


@router.post("/notifications", status_code=status.HTTP_201_CREATED)
def create_notification(payload: NotificationCreate, db: Session = Depends(get_db), profile: Profile = Depends(require_roles("admin", "director", "manager"))) -> dict:
    if payload.severity not in {"info", "success", "warning", "critical"}:
        raise HTTPException(status_code=422, detail="Invalid notification severity")
    item = Notification(**payload.model_dump())
    db.add(item)
    db.flush()
    audit(db, profile, "create", "notification", item.id, f"Notification sent to {item.recipient}")
    db.commit()
    db.refresh(item)
    return row(item)


@router.post("/notifications/{notification_id}/read")
def mark_notification_read(notification_id: uuid.UUID, db: Session = Depends(get_db), profile: Profile = Depends(current_profile)) -> dict:
    item = db.get(Notification, notification_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    if profile.role not in {"admin", "director"} and item.recipient != profile.email_snapshot:
        raise HTTPException(status_code=403, detail="Notification belongs to another user")
    item.read = True
    db.commit()
    db.refresh(item)
    return row(item)


@router.get("/profiles")
def list_profiles(db: Session = Depends(get_db), _: Profile = Depends(require_roles("admin", "director"))) -> list[dict]:
    return [row(item) for item in db.scalars(select(Profile).order_by(Profile.email_snapshot)).all()]


@router.patch("/profiles/{profile_id}/role")
def update_profile_role(profile_id: uuid.UUID, payload: ProfileRoleUpdate, db: Session = Depends(get_db), profile: Profile = Depends(require_roles("admin", "director"))) -> dict:
    if payload.role not in ALLOWED_ROLES:
        raise HTTPException(status_code=422, detail="Unknown role")
    item = db.get(Profile, profile_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    old_role = item.role
    item.role = payload.role
    audit(db, profile, "role", "profile", item.id, f"Changed {item.email_snapshot or item.id} from {old_role} to {payload.role}")
    db.commit()
    db.refresh(item)
    return row(item)


@router.get("/governance-summary")
def governance_summary(db: Session = Depends(get_db), _: Profile = Depends(require_roles("admin", "director", "manager", "accountant"))) -> dict:
    pending_approvals = int(db.scalar(select(func.count()).select_from(ApprovalRequest).where(ApprovalRequest.status == "pending")) or 0)
    unread_notifications = int(db.scalar(select(func.count()).select_from(Notification).where(Notification.read.is_(False))) or 0)
    document_count = int(db.scalar(select(func.count()).select_from(DocumentRecord)) or 0)
    employee_count = int(db.scalar(select(func.count()).select_from(Employee).where(Employee.active.is_(True))) or 0)
    draft_payroll = int(db.scalar(select(func.count()).select_from(PayrollRun).where(PayrollRun.status == "draft")) or 0)
    return {"pending_approvals": pending_approvals, "unread_notifications": unread_notifications, "documents": document_count, "active_employees": employee_count, "draft_payroll_runs": draft_payroll}
