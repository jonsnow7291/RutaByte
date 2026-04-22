from __future__ import annotations

from typing import Annotated, Any, Iterable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.security import ADMIN_ROLE_ID, CAJERO_ROLE_ID, MESERO_ROLE_ID, decode_and_verify_jwt


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def _decode_token_or_401(token: str) -> dict[str, Any]:
    try:
        return decode_and_verify_jwt(token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def _extract_role_id(payload: dict[str, Any]) -> int:
    role_id = payload.get("rol_id", payload.get("role_id"))
    try:
        return int(role_id)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El token no contiene un rol valido",
        ) from exc


def _require_roles(payload: dict[str, Any], allowed_roles: Iterable[int], error_message: str) -> dict[str, Any]:
    role_id = _extract_role_id(payload)
    if role_id not in set(allowed_roles):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_message)
    return payload


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> dict[str, Any]:
    return _decode_token_or_401(token)


def get_current_admin(token: Annotated[str, Depends(oauth2_scheme)]) -> dict[str, Any]:
    payload = _decode_token_or_401(token)
    return _require_roles(payload, {ADMIN_ROLE_ID}, "Acceso denegado. Se requiere rol de Administrador")


def get_current_mesero(token: Annotated[str, Depends(oauth2_scheme)]) -> dict[str, Any]:
    payload = _decode_token_or_401(token)
    return _require_roles(payload, {ADMIN_ROLE_ID, MESERO_ROLE_ID}, "Acceso denegado. Se requiere rol de Mesero o Administrador")


def get_current_cajero(token: Annotated[str, Depends(oauth2_scheme)]) -> dict[str, Any]:
    payload = _decode_token_or_401(token)
    return _require_roles(payload, {ADMIN_ROLE_ID, CAJERO_ROLE_ID}, "Acceso denegado. Se requiere rol de Cajero o Administrador")
