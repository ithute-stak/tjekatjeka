from sqlalchemy import select

from .db import SessionLocal
from .enterprise_finance_models import LedgerAccount
from .models import Branch, Material, Product


DEFAULT_MATERIALS = [
    ("ROUGH-SAND", "Rough sand", "aggregate", "tonne", 5),
    ("SMOOTH-SAND", "Smooth sand", "aggregate", "tonne", 5),
    ("CEMENT", "Cement", "binder", "bag", 40),
    ("WATER", "Water", "utility", "litre", 1000),
]

ALUMINIUM_MATERIALS = [
    ("ALU-PROFILE", "Aluminium profile", "aluminium", "metre", 20),
    ("GLASS-6MM", "6mm clear glass", "glass", "m2", 10),
    ("SILICONE", "Silicone", "consumable", "tube", 10),
    ("HARDWARE", "Locks, handles & hardware", "hardware", "piece", 20),
]

DEFAULT_LEDGER_ACCOUNTS = [
    ("1000", "Cash and bank", "asset"),
    ("1100", "Accounts receivable", "asset"),
    ("1200", "Inventory", "asset"),
    ("2000", "Accounts payable", "liability"),
    ("3000", "Owner equity", "equity"),
    ("4000", "Sales revenue", "income"),
    ("4100", "Delivery revenue", "income"),
    ("5000", "Cost of goods sold", "expense"),
    ("5100", "Operating expenses", "expense"),
    ("5200", "Payroll expense", "expense"),
    ("5300", "Fleet expense", "expense"),
]


def seed_reference_data() -> None:
    with SessionLocal() as db:
        brick = db.scalar(select(Branch).where(Branch.code == "BRICK"))
        if brick is None:
            brick = Branch(code="BRICK", name="Brick Manufacturing & Sales", division="brick")
            db.add(brick)
            db.flush()

        aluminium = db.scalar(select(Branch).where(Branch.code == "ALUMINIUM"))
        if aluminium is None:
            aluminium = Branch(code="ALUMINIUM", name="Aluminium & Glass Works", division="aluminium")
            db.add(aluminium)
            db.flush()

        for code, name, category, unit, reorder in DEFAULT_MATERIALS:
            exists = db.scalar(select(Material).where(Material.branch_id == brick.id, Material.code == code))
            if exists is None:
                db.add(Material(branch_id=brick.id, code=code, name=name, category=category, unit=unit, reorder_level=reorder))

        for code, name, category, unit, reorder in ALUMINIUM_MATERIALS:
            exists = db.scalar(select(Material).where(Material.branch_id == aluminium.id, Material.code == code))
            if exists is None:
                db.add(Material(branch_id=aluminium.id, code=code, name=name, category=category, unit=unit, reorder_level=reorder))

        for code, name, price in [
            ("BLOCK-4", "4-inch block", 0),
            ("BLOCK-6", "6-inch block", 0),
            ("BLOCK-9", "9-inch block", 0),
            ("PAVER", "Paving brick", 0),
        ]:
            exists = db.scalar(select(Product).where(Product.branch_id == brick.id, Product.code == code))
            if exists is None:
                db.add(Product(branch_id=brick.id, code=code, name=name, unit="each", selling_price=price))

        for code, name, account_type in DEFAULT_LEDGER_ACCOUNTS:
            exists = db.scalar(select(LedgerAccount).where(LedgerAccount.code == code))
            if exists is None:
                db.add(LedgerAccount(code=code, name=name, account_type=account_type))

        db.commit()
