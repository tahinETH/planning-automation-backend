from __future__ import annotations

from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from .config import settings


bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    id: str
    name: str


def _display_name(claims: dict) -> str:
    return str(
        claims.get("name")
        or claims.get("full_name")
        or claims.get("email")
        or claims.get("primary_email_address")
        or "Kullanıcı"
    )


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> CurrentUser:
    if settings.auth_disabled:
        return CurrentUser(id="development-user", name="Planlama Kullanıcısı")
    if credentials is None:
        raise HTTPException(status_code=401, detail="Oturum gerekli")
    if not settings.clerk_jwks_url or not settings.clerk_issuer_url:
        raise HTTPException(status_code=503, detail="Clerk yapılandırması tamamlanmadı")
    try:
        signing_key = PyJWKClient(settings.clerk_jwks_url).get_signing_key_from_jwt(credentials.credentials)
        options = {"verify_aud": bool(settings.clerk_audience)}
        claims = jwt.decode(
            credentials.credentials,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.clerk_audience or None,
            issuer=settings.clerk_issuer_url,
            options=options,
        )
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Geçersiz oturum") from exc
    if settings.clerk_authorized_parties and claims.get("azp") not in settings.clerk_authorized_parties:
        raise HTTPException(status_code=401, detail="Yetkisiz uygulama")
    return CurrentUser(id=str(claims["sub"]), name=_display_name(claims))

