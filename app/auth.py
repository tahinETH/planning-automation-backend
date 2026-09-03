from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import lru_cache
import logging
from typing import Any, Literal

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from .config import settings


bearer = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)
TEST_ISSUER = "selsa-planlama-test"
TEST_AUDIENCE = "selsa-planlama-frontend"
AppRole = Literal["admin", "user"]


@dataclass(frozen=True)
class CurrentUser:
    id: str
    name: str
    email: str
    role: AppRole

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


def create_test_session(password: str, role: AppRole = "admin") -> str:
    """Issue a local token only for automated tests."""
    if not settings.auth_test_mode or password != settings.admin_password:
        raise HTTPException(status_code=401, detail="Şifre yanlış")
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": f"test-{role}",
            "fullName": "Test Yöneticisi" if role == "admin" else "Test Kullanıcısı",
            "primaryEmail": f"{role}@example.com",
            "metadata": {"role": role},
            "iat": now,
            "exp": now + timedelta(hours=1),
            "iss": TEST_ISSUER,
            "aud": TEST_AUDIENCE,
        },
        settings.session_secret,
        algorithm="HS256",
    )


@lru_cache(maxsize=1)
def _jwks_client() -> PyJWKClient:
    return PyJWKClient(f"{settings.clerk_issuer}/.well-known/jwks.json", cache_keys=True)


def _decode_clerk_token(token: str) -> dict[str, Any]:
    if not settings.clerk_issuer:
        raise HTTPException(status_code=503, detail="Clerk kimlik doğrulaması yapılandırılmamış")
    try:
        key: Any = settings.clerk_jwt_key or _jwks_client().get_signing_key_from_jwt(token).key
        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            issuer=settings.clerk_issuer,
            options={"verify_aud": False, "require": ["exp", "iat", "iss", "sub"]},
        )
    except (jwt.PyJWTError, ValueError) as exc:
        logger.warning("Clerk session token rejected (%s): %s", type(exc).__name__, exc)
        raise HTTPException(status_code=401, detail="Oturum geçersiz veya süresi dolmuş") from exc
    authorized_party = claims.get("azp")
    if authorized_party and authorized_party not in settings.clerk_authorized_parties:
        logger.warning(
            "Clerk session token authorized party rejected: %s (allowed: %s)",
            authorized_party,
            ", ".join(settings.clerk_authorized_parties),
        )
        raise HTTPException(status_code=401, detail="Oturum bu uygulama için oluşturulmamış")
    if claims.get("sts") == "pending":
        raise HTTPException(status_code=403, detail="Hesap kurulumu henüz tamamlanmamış")
    return claims


def _decode_token(token: str) -> dict[str, Any]:
    if settings.auth_test_mode:
        try:
            return jwt.decode(
                token,
                settings.session_secret,
                algorithms=["HS256"],
                issuer=TEST_ISSUER,
                audience=TEST_AUDIENCE,
            )
        except jwt.PyJWTError as exc:
            raise HTTPException(status_code=401, detail="Oturum geçersiz veya süresi dolmuş") from exc
    return _decode_clerk_token(token)


def _claim_text(claims: dict[str, Any], key: str) -> str:
    value = claims.get(key)
    return value.strip() if isinstance(value, str) else ""


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> CurrentUser:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Oturum gerekli")
    claims = _decode_token(credentials.credentials)
    user_id = _claim_text(claims, "sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Oturum geçersiz")
    metadata = claims.get("metadata") if isinstance(claims.get("metadata"), dict) else {}
    claimed_role = metadata.get("role")
    role: AppRole = "admin" if claimed_role == "admin" or user_id in settings.clerk_admin_user_ids else "user"
    email = _claim_text(claims, "primaryEmail") or _claim_text(claims, "email")
    name = _claim_text(claims, "fullName") or _claim_text(claims, "name") or email or "Selsa Kullanıcısı"
    return CurrentUser(id=user_id, name=name, email=email, role=role)


def require_admin(user: CurrentUser = Depends(current_user)) -> CurrentUser:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Bu işlem yalnızca yöneticiler tarafından yapılabilir")
    return user
