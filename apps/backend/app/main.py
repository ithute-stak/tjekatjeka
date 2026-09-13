import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from redis import Redis
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from .auth import current_claims
from .config import settings
from .db import engine, get_db
from .models import Profile
from .operations import router as operations_router
from .seed import seed_reference_data


@asynccontextmanager
async def lifespan(_: FastAPI):
    seed_reference_data()
    yield


app = FastAPI(
    title="Tjekatjeka Holdings API",
    version="1.0.0",
    redoc_url=None,
    lifespan=lifespan,
)
app.include_router(operations_router)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "tjekatjeka-api"}


@app.get("/readyz")
def readyz() -> dict[str, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        redis_client = Redis.from_url(settings.redis_url, socket_connect_timeout=2, socket_timeout=2)
        redis_client.ping()
        redis_client.close()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="dependency unavailable") from exc
    return {"status": "ready", "database": "ok", "redis": "ok"}


@app.get("/api/v1/me")
def me(claims: dict = Depends(current_claims), db: Session = Depends(get_db)) -> dict:
    auth_user_id = uuid.UUID(str(claims["sub"]))
    email_value = claims.get("email")
    email = str(email_value).strip().lower() if email_value else None

    profile = db.scalar(select(Profile).where(Profile.auth_user_id == auth_user_id))
    if profile is None:
        bootstrap = settings.bootstrap_admin_email.strip().lower()
        bypass_user = settings.dev_auth_bypass and email == "dev@tjekatjeka.local"
        if not bypass_user and (not bootstrap or email != bootstrap):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tjekatjeka account is not provisioned; configure the bootstrap administrator first",
            )
        profile = Profile(auth_user_id=auth_user_id, email_snapshot=email, role="admin")
        db.add(profile)
        db.commit()
        db.refresh(profile)
    elif email and profile.email_snapshot != email:
        profile.email_snapshot = email
        db.commit()

    return {
        "id": str(profile.id),
        "auth_user_id": str(profile.auth_user_id),
        "email": profile.email_snapshot,
        "role": profile.role,
    }
