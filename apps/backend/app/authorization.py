import uuid
from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import current_claims
from .config import settings
from .db import get_db
from .models import Profile

ALLOWED_ROLES = {
    "admin",
    "director",
    "manager",
    "accountant",
    "brick_manager",
    "aluminium_manager",
    "storekeeper",
    "sales",
    "fleet_manager",
    "hr",
    "driver",
    "viewer",
}

WRITE_PERMISSIONS = [
    ("/api/v1/materials", {"admin", "director", "manager", "brick_manager", "aluminium_manager", "storekeeper"}),
    ("/api/v1/purchases", {"admin", "director", "manager", "accountant", "storekeeper"}),
    ("/api/v1/expenses", {"admin", "director", "manager", "accountant"}),
    ("/api/v1/production", {"admin", "director", "manager", "brick_manager"}),
    ("/api/v1/aluminium-jobs", {"admin", "director", "manager", "aluminium_manager", "sales"}),
    ("/api/v1/vehicles", {"admin", "director", "manager", "fleet_manager"}),
    ("/api/v1/fuel", {"admin", "director", "manager", "fleet_manager", "driver"}),
    ("/api/v1/maintenance", {"admin", "director", "manager", "fleet_manager"}),
    ("/api/v1/sales", {"admin", "director", "manager", "accountant", "sales"}),
    ("/api/v1/customers", {"admin", "director", "manager", "accountant", "sales"}),
    ("/api/v1/customer-invoices", {"admin", "director", "manager", "accountant", "sales"}),
    ("/api/v1/customer-payments", {"admin", "director", "manager", "accountant"}),
    ("/api/v1/suppliers", {"admin", "director", "manager", "accountant", "storekeeper"}),
    ("/api/v1/supplier-bills", {"admin", "director", "manager", "accountant"}),
    ("/api/v1/supplier-payments", {"admin", "director", "manager", "accountant"}),
    ("/api/v1/brick-recipes", {"admin", "director", "manager", "brick_manager"}),
    ("/api/v1/aluminium-measurements", {"admin", "director", "manager", "aluminium_manager"}),
    ("/api/v1/deliveries", {"admin", "director", "manager", "fleet_manager", "driver", "sales"}),
]


def current_profile(
    claims: dict = Depends(current_claims),
    db: Session = Depends(get_db),
) -> Profile:
    auth_user_id = uuid.UUID(str(claims["sub"]))
    email_value = claims.get("email")
    email = str(email_value).strip().lower() if email_value else None
    profile = db.scalar(select(Profile).where(Profile.auth_user_id == auth_user_id))
    if profile is None:
        bootstrap = settings.bootstrap_admin_email.strip().lower()
        bypass_user = settings.dev_auth_bypass and email == "dev@tjekatjeka.local"
        if not bypass_user and (not bootstrap or email != bootstrap):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tjekatjeka account is not provisioned")
        profile = Profile(auth_user_id=auth_user_id, email_snapshot=email, role="admin")
        db.add(profile)
        db.commit()
        db.refresh(profile)
    elif email and profile.email_snapshot != email:
        profile.email_snapshot = email
        db.commit()
    return profile


def require_roles(*roles: str) -> Callable:
    allowed = set(roles)

    def dependency(profile: Profile = Depends(current_profile)) -> Profile:
        if profile.role not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient Tjekatjeka permission")
        return profile

    return dependency


def enforce_route_permission(request: Request, profile: Profile = Depends(current_profile)) -> Profile:
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return profile
    path = request.url.path
    allowed = {"admin", "director", "manager"}
    for prefix, roles in WRITE_PERMISSIONS:
        if path.startswith(prefix):
            allowed = roles
            break
    if profile.role not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your Tjekatjeka role cannot modify this module")
    return profile
