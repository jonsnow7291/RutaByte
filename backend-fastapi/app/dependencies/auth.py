from __future__ import annotations

from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.security import ADMIN_ROLE_ID, decode_and_verify_jwt


MESERO_ROLE_ID = 3

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> dict[str, Any]:
    try:
        payload = decode_and_verify_jwt(token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    return payload


def get_current_admin(token: Annotated[str, Depends(oauth2_scheme)]) -> dict[str, Any]:
    try:
        payload = decode_and_verify_jwt(token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    role_id = payload.get("rol_id", payload.get("role_id"))
    try:
        role_id_int = int(role_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El token no contiene un rol valido para Administrador",
        )

    if role_id_int != ADMIN_ROLE_ID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Se requiere rol de Administrador",
        )

    return payload


def get_current_mesero(token: Annotated[str, Depends(oauth2_scheme)]) -> dict[str, Any]:
    try:
        payload = decode_and_verify_jwt(token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    role_id = payload.get("rol_id", payload.get("role_id"))
    try:
        role_id_int = int(role_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El token no contiene un rol valido",
        )

    if role_id_int != MESERO_ROLE_ID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Se requiere rol de Mesero",
        )

    return payload
