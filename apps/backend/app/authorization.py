import uuid
from collections.abc import Callable

from fastapi import Depends, HTTPException, status
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
