from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings


bearer = HTTPBearer(auto_error=False)
ISSUER = "selsa-planlama-api"
AUDIENCE = "selsa-planlama-frontend"


@dataclass(frozen=True)
class CurrentUser:
    id: str
    name: str


def create_session(password: str) -> str:
    if not secrets.compare_digest(password, settings.admin_password):
        raise HTTPException(status_code=401, detail="Şifre yanlış")
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": "planning-admin", "name": "Planlama Yöneticisi", "iat": now, "exp": now + timedelta(days=settings.session_days), "iss": ISSUER, "aud": AUDIENCE},
        settings.session_secret,
        algorithm="HS256",
    )


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> CurrentUser:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Oturum gerekli")
    try:
        claims = jwt.decode(credentials.credentials, settings.session_secret, algorithms=["HS256"], issuer=ISSUER, audience=AUDIENCE)
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Oturum geçersiz veya süresi dolmuş") from exc
    if claims.get("sub") != "planning-admin":
        raise HTTPException(status_code=401, detail="Oturum geçersiz")
    return CurrentUser(id="planning-admin", name=str(claims.get("name") or "Planlama Yöneticisi"))
