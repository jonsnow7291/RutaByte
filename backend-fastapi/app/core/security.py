from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt import exceptions as jwt_exceptions


SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
TOKEN_ALGORITHM = "RS256"
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_HOURS", "8"))
ADMIN_ROLE_ID = int(os.getenv("ADMIN_ROLE_ID", "1"))


@lru_cache(maxsize=1)
def _load_rsa_keypair() -> tuple[str, str]:
    private_key = os.getenv("JWT_PRIVATE_KEY")
    public_key = os.getenv("JWT_PUBLIC_KEY")
    if private_key and public_key:
        return private_key, public_key

    private_key_path = os.getenv("JWT_PRIVATE_KEY_PATH")
    public_key_path = os.getenv("JWT_PUBLIC_KEY_PATH")
    if private_key_path and public_key_path and os.path.exists(private_key_path) and os.path.exists(public_key_path):
        with open(private_key_path, "r", encoding="utf-8") as private_file:
            loaded_private_key = private_file.read()
        with open(public_key_path, "r", encoding="utf-8") as public_file:
            loaded_public_key = public_file.read()
        return loaded_private_key, loaded_public_key

    generated = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = generated.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = generated.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_pem.decode("utf-8"), public_pem.decode("utf-8")


def create_access_token(payload: dict[str, Any], expires_hours: int = ACCESS_TOKEN_EXPIRE_HOURS) -> str:
    private_key, _ = _load_rsa_keypair()
    now = datetime.now(timezone.utc)
    claims = dict(payload)
    claims["iat"] = int(now.timestamp())
    claims["exp"] = int((now + timedelta(hours=expires_hours)).timestamp())
    return jwt.encode(claims, private_key, algorithm=TOKEN_ALGORITHM)


def decode_and_verify_jwt(token: str) -> dict[str, Any]:
    _, public_key = _load_rsa_keypair()

    try:
        payload = jwt.decode(token, public_key, algorithms=[TOKEN_ALGORITHM])
        return dict(payload)
    except jwt_exceptions.PyJWTError:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return dict(payload)
        except jwt_exceptions.PyJWTError as exc:
            raise ValueError("Token JWT invalido o expirado") from exc
