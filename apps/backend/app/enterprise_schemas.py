import uuid
from datetime import date

from pydantic import BaseModel, Field


class QuoteLineCreate(BaseModel):
    description: str = Field(min_length=1, max_length=240)
    quantity: float = Field(gt=0)
    unit: str = Field(default="each", min_length=1, max_length=30)
    unit_price: float = Field(ge=0)


class QuoteCreate(BaseModel):
    branch_id: uuid.UUID | None = None
    customer_id: uuid.UUID
    quote_no: str = Field(min_length=2, max_length=80)
    description: str | None = None
    tax_amount: float = Field(default=0, ge=0)
    quote_date: date = Field(default_factory=date.today)
    valid_until: date | None = None
    lines: list[QuoteLineCreate] = Field(min_length=1)


class QuoteStatusUpdate(BaseModel):
    status: str


class QuoteConvert(BaseModel):
    invoice_no: str = Field(min_length=2, max_length=80)
    due_date: date | None = None


class LedgerAccountCreate(BaseModel):
    code: str = Field(min_length=2, max_length=30)
    name: str = Field(min_length=2, max_length=140)
    account_type: str


class JournalLineCreate(BaseModel):
    account_id: uuid.UUID
    debit: float = Field(default=0, ge=0)
    credit: float = Field(default=0, ge=0)
    memo: str | None = None


class JournalEntryCreate(BaseModel):
    reference: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=2, max_length=240)
    entry_date: date = Field(default_factory=date.today)
    source_type: str | None = None
    source_id: uuid.UUID | None = None
    lines: list[JournalLineCreate] = Field(min_length=2)


class BankAccountCreate(BaseModel):
    name: str
    bank_name: str
    account_mask: str
    currency: str = "LSL"
    opening_balance: float = 0


class BankTransactionCreate(BaseModel):
    bank_account_id: uuid.UUID
    transaction_date: date = Field(default_factory=date.today)
    description: str
    reference: str | None = None
    amount: float = Field(gt=0)
    direction: str
    journal_entry_id: uuid.UUID | None = None


class EmployeeCreate(BaseModel):
    branch_id: uuid.UUID | None = None
    employee_no: str
    full_name: str
    job_title: str
    phone: str | None = None
    email: str | None = None
    basic_salary: float = Field(default=0, ge=0)
    hired_date: date = Field(default_factory=date.today)


class PayslipInput(BaseModel):
    employee_id: uuid.UUID
    allowances: float = Field(default=0, ge=0)
    deductions: float = Field(default=0, ge=0)
    notes: str | None = None


class PayrollRunCreate(BaseModel):
    period_label: str
    pay_date: date
    payslips: list[PayslipInput] = Field(min_length=1)


class PayrollStatusUpdate(BaseModel):
    status: str


class ApprovalCreate(BaseModel):
    entity_type: str
    entity_id: uuid.UUID | None = None
    title: str
    amount: float | None = Field(default=None, ge=0)


class ApprovalDecision(BaseModel):
    status: str
    decision_note: str | None = None


class DocumentCreate(BaseModel):
    entity_type: str
    entity_id: uuid.UUID | None = None
    title: str
    document_type: str
    storage_url: str


class NotificationCreate(BaseModel):
    recipient: str
    title: str
    message: str
    severity: str = "info"


class ProfileRoleUpdate(BaseModel):
    role: str
