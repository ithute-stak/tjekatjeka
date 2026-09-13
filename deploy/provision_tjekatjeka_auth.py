#!/usr/bin/env python3
"""Provision Tjekatjeka's first-party Auth client and owner account.

Run only inside the central Ithute Auth container. The password is read from
stdin so it never appears in a command line or deployment log.
"""
from __future__ import annotations

import os
import sys

from sqlalchemy import select, update

from app.db import SessionLocal
from app.models import Application, AuthSession, User, utcnow
from app.security import hash_password, normalize_email, verify_password

CLIENT_ID = "tjekatjeka"
CLIENT_NAME = "Tjekatjeka Holdings"


def main() -> int:
    email = normalize_email(os.environ.get("TJEKATJEKA_ADMIN_EMAIL", ""))
    password = sys.stdin.read().rstrip("\r\n")
    if not email or "@" not in email:
        raise SystemExit("TJEKATJEKA_ADMIN_EMAIL must be a valid email")
    if len(password) < 12 or len(password) > 128:
        raise SystemExit("Owner password must be between 12 and 128 characters")

    now = utcnow()
    with SessionLocal() as db:
        app = db.scalar(select(Application).where(Application.client_id == CLIENT_ID))
        if app is None:
            app = Application(client_id=CLIENT_ID, name=CLIENT_NAME, is_active=True)
            db.add(app)
        else:
            app.name = CLIENT_NAME
            app.is_active = True

        user = db.scalar(select(User).where(User.email == email))
        created = user is None
        password_changed = False
        if user is None:
            user = User(
                email=email,
                phone=None,
                display_name="Tjekatjeka System Owner",
                password_hash=hash_password(password),
                is_active=True,
                email_verified=True,
            )
            db.add(user)
            db.flush()
            password_changed = True
        else:
            user.is_active = True
            user.email_verified = True
            user.failed_login_attempts = 0
            user.locked_until = None
            if not user.display_name.strip():
                user.display_name = "Tjekatjeka System Owner"
            if not verify_password(password, user.password_hash):
                user.password_hash = hash_password(password)
                user.password_changed_at = now
                user.security_version += 1
                password_changed = True

        if password_changed:
            db.execute(
                update(AuthSession)
                .where(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None))
                .values(revoked_at=now, revoked_reason="tjekatjeka_owner_password_provisioned")
            )

        db.commit()
        action = "created" if created else ("updated" if password_changed else "verified")
        print(f"Tjekatjeka central-auth client ready; owner account {action}: {email}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
