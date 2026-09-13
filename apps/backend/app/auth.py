import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from .config import settings


bearer = HTTPBearer(auto_error=False)
_jwks = PyJWKClient(f"{settings.auth_issuer.rstrip('/')}/.well-known/jwks.json")


def current_claims(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> dict:
    if settings.dev_auth_bypass and credentials is None:
        return {
            "sub": str(uuid.UUID("11111111-1111-4111-8111-111111111111")),
            "email": "dev@tjekatjeka.local",
            "aud": settings.auth_audience,
        }

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    try:
        signing_key = _jwks.get_signing_key_from_jwt(credentials.credentials)
        payload = jwt.decode(
            credentials.credentials,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.auth_audience,
            issuer=settings.auth_issuer.rstrip("/"),
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token") from exc

    if not payload.get("sub"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token subject is missing")
    return payload
