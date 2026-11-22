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


def test_clerk_rs256_token_tolerates_small_clock_skew_and_rejects_large_skew() -> None:
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

    def make_token(iat_offset_seconds: int, nbf_offset_seconds: int, exp_offset_seconds: int) -> HTTPAuthorizationCredentials:
        token = jwt.encode(
            {
                "sub": "user_clock_skew",
                "fullName": "Saat Testi",
                "primaryEmail": "saat@example.com",
                "metadata": {"role": "admin"},
                "azp": "http://localhost:3001",
                "iss": "https://test.clerk.accounts.dev",
                "iat": now + timedelta(seconds=iat_offset_seconds),
                "nbf": now + timedelta(seconds=nbf_offset_seconds),
                "exp": now + timedelta(seconds=exp_offset_seconds),
            },
            private_key,
            algorithm="RS256",
        )
        return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    try:
        _set_setting("auth_test_mode", False)
        _set_setting("clerk_issuer", "https://test.clerk.accounts.dev")
        _set_setting("clerk_jwt_key", public_key)
        _set_setting("clerk_authorized_parties", ("http://localhost:3001",))

        # 2s ahead of local clock (e.g. macOS NTP drift) stays within 5s leeway.
        user = current_user(make_token(iat_offset_seconds=2, nbf_offset_seconds=2, exp_offset_seconds=60))
        assert user.id == "user_clock_skew"
        assert user.role == "admin"

        # 10s ahead of local clock is still rejected.
        with pytest.raises(HTTPException) as immature:
            current_user(make_token(iat_offset_seconds=10, nbf_offset_seconds=10, exp_offset_seconds=60))
        assert immature.value.status_code == 401

        # 10s past expiration is still rejected.
        with pytest.raises(HTTPException) as expired:
            current_user(make_token(iat_offset_seconds=-70, nbf_offset_seconds=-70, exp_offset_seconds=-10))
        assert expired.value.status_code == 401
    finally:
        for name, value in originals.items():
            _set_setting(name, value)
