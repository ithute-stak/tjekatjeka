import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .accounting_models import CustomerInvoice
from .authorization import current_profile, require_roles
from .db import get_db
from .enterprise_admin_models import AuditEvent
from .enterprise_finance_models import BankAccount, BankTransaction, JournalEntry, JournalLine, LedgerAccount, Quote, QuoteLine
from .enterprise_schemas import BankAccountCreate, BankTransactionCreate, JournalEntryCreate, LedgerAccountCreate, QuoteConvert, QuoteCreate, QuoteStatusUpdate
from .models import Customer, Profile

router = APIRouter(prefix="/api/v1", dependencies=[Depends(current_profile)])


def row(model) -> dict:
    return {column.name: getattr(model, column.name) for column in model.__table__.columns}


def audit(db: Session, profile: Profile, action: str, entity_type: str, entity_id: uuid.UUID | None, summary: str) -> None:
    db.add(AuditEvent(actor=profile.email_snapshot, action=action, entity_type=entity_type, entity_id=entity_id, summary=summary))


def quote_row(item: Quote, db: Session) -> dict:
    data = row(item)
    data["lines"] = [row(line) for line in db.scalars(select(QuoteLine).where(QuoteLine.quote_id == item.id).order_by(QuoteLine.description)).all()]
    customer = db.get(Customer, item.customer_id)
    data["customer_name"] = customer.name if customer else "Unknown"
    return data


@router.get("/quotes")
def list_quotes(db: Session = Depends(get_db)) -> list[dict]:
    return [quote_row(item, db) for item in db.scalars(select(Quote).order_by(Quote.quote_date.desc(), Quote.quote_no.desc())).all()]


@router.post("/quotes", status_code=status.HTTP_201_CREATED)
def create_quote(payload: QuoteCreate, db: Session = Depends(get_db), profile: Profile = Depends(require_roles("admin", "director", "manager", "sales", "aluminium_manager"))) -> dict:
    if db.get(Customer, payload.customer_id) is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    if db.scalar(select(Quote).where(Quote.quote_no == payload.quote_no)):
        raise HTTPException(status_code=409, detail="Quote number already exists")
    subtotal = sum(item.quantity * item.unit_price for item in payload.lines)
    quote = Quote(branch_id=payload.branch_id, customer_id=payload.customer_id, quote_no=payload.quote_no, description=payload.description, subtotal=subtotal, tax_amount=payload.tax_amount, total_amount=subtotal + payload.tax_amount, quote_date=payload.quote_date, valid_until=payload.valid_until)
    db.add(quote)
    db.flush()
    for item in payload.lines:
        db.add(QuoteLine(quote_id=quote.id, description=item.description, quantity=item.quantity, unit=item.unit, unit_price=item.unit_price, line_total=item.quantity * item.unit_price))
    audit(db, profile, "create", "quote", quote.id, f"Created quote {quote.quote_no} for M{float(quote.total_amount):.2f}")
    db.commit()
    db.refresh(quote)
    return quote_row(quote, db)


@router.patch("/quotes/{quote_id}")
def update_quote_status(quote_id: uuid.UUID, payload: QuoteStatusUpdate, db: Session = Depends(get_db), profile: Profile = Depends(require_roles("admin", "director", "manager", "sales", "aluminium_manager"))) -> dict:
    quote = db.get(Quote, quote_id)
    if quote is None:
        raise HTTPException(status_code=404, detail="Quote not found")
    if payload.status not in {"draft", "sent", "accepted", "rejected", "expired"}:
        raise HTTPException(status_code=422, detail="Invalid quote status")
    if quote.converted_invoice_id:
        raise HTTPException(status_code=409, detail="Converted quote cannot be changed")
    quote.status = payload.status
    audit(db, profile, "status", "quote", quote.id, f"Quote {quote.quote_no} changed to {payload.status}")
    db.commit()
    db.refresh(quote)
    return quote_row(quote, db)


@router.post("/quotes/{quote_id}/convert")
def convert_quote(quote_id: uuid.UUID, payload: QuoteConvert, db: Session = Depends(get_db), profile: Profile = Depends(require_roles("admin", "director", "manager", "accountant", "sales"))) -> dict:
    quote = db.get(Quote, quote_id)
    if quote is None:
        raise HTTPException(status_code=404, detail="Quote not found")
    if quote.converted_invoice_id:
        invoice = db.get(CustomerInvoice, quote.converted_invoice_id)
        return {"quote": quote_row(quote, db), "invoice": row(invoice) if invoice else None}
    if quote.status in {"rejected", "expired"}:
        raise HTTPException(status_code=409, detail="Rejected or expired quote cannot be invoiced")
    if db.scalar(select(CustomerInvoice).where(CustomerInvoice.invoice_no == payload.invoice_no)):
        raise HTTPException(status_code=409, detail="Invoice number already exists")
    invoice = CustomerInvoice(customer_id=quote.customer_id, branch_id=quote.branch_id, invoice_no=payload.invoice_no, description=quote.description or f"Converted from quote {quote.quote_no}", amount=quote.total_amount, due_date=payload.due_date)
    db.add(invoice)
    db.flush()
    quote.converted_invoice_id = invoice.id
    quote.status = "converted"
    audit(db, profile, "convert", "quote", quote.id, f"Converted {quote.quote_no} to invoice {invoice.invoice_no}")
    db.commit()
    db.refresh(invoice)
    return {"quote": quote_row(quote, db), "invoice": row(invoice)}


@router.get("/ledger-accounts")
def list_ledger_accounts(db: Session = Depends(get_db)) -> list[dict]:
    return [row(item) for item in db.scalars(select(LedgerAccount).order_by(LedgerAccount.code)).all()]


@router.post("/ledger-accounts", status_code=status.HTTP_201_CREATED)
def create_ledger_account(payload: LedgerAccountCreate, db: Session = Depends(get_db), profile: Profile = Depends(require_roles("admin", "director", "accountant"))) -> dict:
    if payload.account_type not in {"asset", "liability", "equity", "income", "expense"}:
        raise HTTPException(status_code=422, detail="Invalid account type")
    if db.scalar(select(LedgerAccount).where(LedgerAccount.code == payload.code)):
        raise HTTPException(status_code=409, detail="Account code already exists")
    item = LedgerAccount(**payload.model_dump())
    db.add(item)
    db.flush()
    audit(db, profile, "create", "ledger_account", item.id, f"Created account {item.code} {item.name}")
    db.commit()
    db.refresh(item)
    return row(item)


@router.get("/journals")
def list_journals(db: Session = Depends(get_db)) -> list[dict]:
    result = []
    for entry in db.scalars(select(JournalEntry).order_by(JournalEntry.entry_date.desc(), JournalEntry.posted_at.desc()).limit(250)).all():
        data = row(entry)
        lines = [row(line) for line in db.scalars(select(JournalLine).where(JournalLine.entry_id == entry.id)).all()]
        data["lines"] = lines
        data["debit_total"] = sum(float(line["debit"]) for line in lines)
        data["credit_total"] = sum(float(line["credit"]) for line in lines)
        result.append(data)
    return result


@router.post("/journals", status_code=status.HTTP_201_CREATED)
def create_journal(payload: JournalEntryCreate, db: Session = Depends(get_db), profile: Profile = Depends(require_roles("admin", "director", "accountant"))) -> dict:
    debit_total = sum(item.debit for item in payload.lines)
    credit_total = sum(item.credit for item in payload.lines)
    if debit_total <= 0 or abs(debit_total - credit_total) > 0.005:
        raise HTTPException(status_code=422, detail="Journal must be balanced and greater than zero")
    for item in payload.lines:
        if item.debit and item.credit:
            raise HTTPException(status_code=422, detail="A journal line cannot contain both debit and credit")
        if db.get(LedgerAccount, item.account_id) is None:
            raise HTTPException(status_code=404, detail=f"Ledger account {item.account_id} not found")
    if db.scalar(select(JournalEntry).where(JournalEntry.reference == payload.reference)):
        raise HTTPException(status_code=409, detail="Journal reference already exists")
    entry = JournalEntry(reference=payload.reference, description=payload.description, entry_date=payload.entry_date, source_type=payload.source_type, source_id=payload.source_id, posted_by=profile.email_snapshot)
    db.add(entry)
    db.flush()
    for item in payload.lines:
        db.add(JournalLine(entry_id=entry.id, **item.model_dump()))
    audit(db, profile, "post", "journal_entry", entry.id, f"Posted balanced journal {entry.reference} for M{debit_total:.2f}")
    db.commit()
    db.refresh(entry)
    data = row(entry)
    data.update(debit_total=debit_total, credit_total=credit_total)
    return data


@router.get("/trial-balance")
def trial_balance(db: Session = Depends(get_db)) -> dict:
    accounts = []
    total_debit = total_credit = 0.0
    for account in db.scalars(select(LedgerAccount).order_by(LedgerAccount.code)).all():
        debit = float(db.scalar(select(func.coalesce(func.sum(JournalLine.debit), 0)).where(JournalLine.account_id == account.id)) or 0)
        credit = float(db.scalar(select(func.coalesce(func.sum(JournalLine.credit), 0)).where(JournalLine.account_id == account.id)) or 0)
        total_debit += debit
        total_credit += credit
        accounts.append({**row(account), "debit": debit, "credit": credit, "balance": debit - credit})
    return {"accounts": accounts, "total_debit": total_debit, "total_credit": total_credit, "balanced": abs(total_debit - total_credit) < 0.005}


@router.get("/bank-accounts")
def list_bank_accounts(db: Session = Depends(get_db)) -> list[dict]:
    result = []
    for account in db.scalars(select(BankAccount).order_by(BankAccount.name)).all():
        inflow = float(db.scalar(select(func.coalesce(func.sum(BankTransaction.amount), 0)).where(BankTransaction.bank_account_id == account.id, BankTransaction.direction == "in")) or 0)
        outflow = float(db.scalar(select(func.coalesce(func.sum(BankTransaction.amount), 0)).where(BankTransaction.bank_account_id == account.id, BankTransaction.direction == "out")) or 0)
        unreconciled = int(db.scalar(select(func.count()).select_from(BankTransaction).where(BankTransaction.bank_account_id == account.id, BankTransaction.reconciled.is_(False))) or 0)
        result.append({**row(account), "balance": float(account.opening_balance) + inflow - outflow, "unreconciled": unreconciled})
    return result


@router.post("/bank-accounts", status_code=status.HTTP_201_CREATED)
def create_bank_account(payload: BankAccountCreate, db: Session = Depends(get_db), profile: Profile = Depends(require_roles("admin", "director", "accountant"))) -> dict:
    account = BankAccount(**payload.model_dump())
    db.add(account)
    db.flush()
    audit(db, profile, "create", "bank_account", account.id, f"Created bank account {account.name}")
    db.commit()
    db.refresh(account)
    return row(account)


@router.get("/bank-transactions")
def list_bank_transactions(db: Session = Depends(get_db)) -> list[dict]:
    return [row(item) for item in db.scalars(select(BankTransaction).order_by(BankTransaction.transaction_date.desc())).all()]


@router.post("/bank-transactions", status_code=status.HTTP_201_CREATED)
def create_bank_transaction(payload: BankTransactionCreate, db: Session = Depends(get_db), profile: Profile = Depends(require_roles("admin", "director", "accountant"))) -> dict:
    if payload.direction not in {"in", "out"}:
        raise HTTPException(status_code=422, detail="Bank transaction direction must be in or out")
    if db.get(BankAccount, payload.bank_account_id) is None:
        raise HTTPException(status_code=404, detail="Bank account not found")
    if payload.journal_entry_id and db.get(JournalEntry, payload.journal_entry_id) is None:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    transaction = BankTransaction(**payload.model_dump())
    db.add(transaction)
    db.flush()
    audit(db, profile, "create", "bank_transaction", transaction.id, f"Recorded bank {transaction.direction} M{float(transaction.amount):.2f}")
    db.commit()
    db.refresh(transaction)
    return row(transaction)


@router.post("/bank-transactions/{transaction_id}/reconcile")
def reconcile_bank_transaction(transaction_id: uuid.UUID, db: Session = Depends(get_db), profile: Profile = Depends(require_roles("admin", "director", "accountant"))) -> dict:
    transaction = db.get(BankTransaction, transaction_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Bank transaction not found")
    transaction.reconciled = True
    transaction.reconciled_at = datetime.now(timezone.utc)
    audit(db, profile, "reconcile", "bank_transaction", transaction.id, f"Reconciled bank transaction {transaction.reference or transaction.id}")
    db.commit()
    db.refresh(transaction)
    return row(transaction)
