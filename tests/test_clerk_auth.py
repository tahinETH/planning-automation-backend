from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.auth import current_user
from app.config import settings


def _set_setting(name: str, value) -> None:
    object.__setattr__(settings, name, value)


def test_clerk_rs256_token_drives_identity_and_role() -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    originals = {
        "auth_test_mode": settings.auth_test_mode,
        "clerk_issuer": settings.clerk_issuer,
        "clerk_jwt_key": settings.clerk_jwt_key,
        "clerk_authorized_parties": settings.clerk_authorized_parties,
    }
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": "user_clerk_admin",
            "fullName": "Ayşe Planlamacı",
            "primaryEmail": "ayse@example.com",
            "metadata": {"role": "admin"},
            "azp": "https://planning.example.com",
            "iss": "https://test.clerk.accounts.dev",
            "iat": now,
            "exp": now + timedelta(minutes=5),
        },
        private_key,
        algorithm="RS256",
    )
    try:
        _set_setting("auth_test_mode", False)
        _set_setting("clerk_issuer", "https://test.clerk.accounts.dev")
        _set_setting("clerk_jwt_key", public_key)
        _set_setting("clerk_authorized_parties", ("https://planning.example.com",))
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        user = current_user(credentials)
        assert user.id == "user_clerk_admin"
        assert user.name == "Ayşe Planlamacı"
        assert user.email == "ayse@example.com"
        assert user.role == "admin"

        _set_setting("clerk_authorized_parties", ("https://other.example.com",))
        with pytest.raises(HTTPException) as rejected:
            current_user(credentials)
        assert rejected.value.status_code == 401
    finally:
        for name, value in originals.items():
            _set_setting(name, value)


def test_clerk_public_metadata_can_assign_admin_role() -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    originals = {
        "auth_test_mode": settings.auth_test_mode,
        "clerk_issuer": settings.clerk_issuer,
        "clerk_jwt_key": settings.clerk_jwt_key,
        "clerk_authorized_parties": settings.clerk_authorized_parties,
    }
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": "user_public_metadata_admin",
            "public_metadata": {"role": "admin"},
            "azp": "https://planning.example.com",
            "iss": "https://test.clerk.accounts.dev",
            "iat": now,
            "exp": now + timedelta(minutes=5),
        },
        private_key,
        algorithm="RS256",
    )
    try:
        _set_setting("auth_test_mode", False)
        _set_setting("clerk_issuer", "https://test.clerk.accounts.dev")
        _set_setting("clerk_jwt_key", public_key)
        _set_setting("clerk_authorized_parties", ("https://planning.example.com",))
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        assert current_user(credentials).role == "admin"
    finally:
        for name, value in originals.items():
            _set_setting(name, value)
