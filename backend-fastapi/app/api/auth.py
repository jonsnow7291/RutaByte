from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from passlib.context import CryptContext
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.email import send_recovery_email
from app.core.security import ACCESS_TOKEN_EXPIRE_HOURS, create_access_token
from app.db.session import get_db
from app.models.auditoria import RegistroAuditoria
from app.models.token_recuperacion import TokenRecuperacion
from app.models.usuario import Usuario
from app.schemas.auth import LoginRequest, RecuperarRequest, ResetPasswordRequest, TokenResponse


router = APIRouter(prefix="/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def _extract_client_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    if request.client is None:
        return None

    return request.client.host


def _verify_password(raw_password: str, password_hash: str) -> bool:
    try:
        return pwd_context.verify(raw_password, password_hash)
    except Exception:
        return False


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    usuario = db.scalar(
        select(Usuario).where(
            func.lower(Usuario.correo) == payload.correo,
            Usuario.activo.is_(True),
        )
    )

    if usuario and usuario.bloqueado_hasta:
        ahora = datetime.now()
        if ahora < usuario.bloqueado_hasta:
            diferencia = usuario.bloqueado_hasta - ahora
            minutos_restantes = int(diferencia.total_seconds() / 60) + 1
            db.add(
                RegistroAuditoria(
                    usuario_id=usuario.id,
                    tipo_evento="LOGIN_FALLIDO",
                    direccion_ip=_extract_client_ip(request),
                )
            )
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cuenta bloqueada temporalmente por exceso de intentos fallidos. Intente en {minutos_restantes} minutos.",
            )

    credenciales_validas = bool(usuario) and _verify_password(payload.contrasena, usuario.hash_contrasena)
    evento = "LOGIN_EXITOSO" if credenciales_validas else "LOGIN_FALLIDO"

    mensaje_adicional = ""
    if usuario:
        if credenciales_validas:
            usuario.intentos_fallidos = 0
            usuario.bloqueado_hasta = None
        else:
            usuario.intentos_fallidos += 1
            if usuario.intentos_fallidos >= 5:
                usuario.bloqueado_hasta = datetime.now() + timedelta(minutes=15)
                mensaje_adicional = " Cuenta bloqueada por 15 minutos."
            else:
                intentos_restantes = 5 - usuario.intentos_fallidos
                mensaje_adicional = f" Intentos restantes: {intentos_restantes}."

    db.add(
        RegistroAuditoria(
            usuario_id=usuario.id if usuario else None,
            tipo_evento=evento,
            direccion_ip=_extract_client_ip(request),
        )
    )
    db.commit()

    if not credenciales_validas or usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Credenciales invalidas.{mensaje_adicional}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        {
            "sub": usuario.correo,
            "correo": usuario.correo,
            "usuario_id": usuario.id,
            "rol_id": usuario.rol_id,
            "sede_id": usuario.sede_id,
        }
    )

    return TokenResponse(
        access_token=token,
        rol_id=usuario.rol_id,
        sede_id=usuario.sede_id,
        expires_in=ACCESS_TOKEN_EXPIRE_HOURS * 60 * 60,
    )


RECOVERY_TOKEN_EXPIRE_MINUTES = 15


@router.post("/recuperar")
def solicitar_recuperacion(payload: RecuperarRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    usuario = db.scalar(
        select(Usuario).where(
            func.lower(Usuario.correo) == payload.correo,
            Usuario.activo.is_(True),
        )
    )

    if usuario is None:
        return {"message": "Si el correo existe, se genero un token de recuperacion."}

    token_str = secrets.token_urlsafe(48)[:64]

    db.add(
        TokenRecuperacion(
            usuario_id=usuario.id,
            token=token_str,
            usado=False,
            expira_en=datetime.now(timezone.utc).replace(tzinfo=None)
            + timedelta(minutes=RECOVERY_TOKEN_EXPIRE_MINUTES),
        )
    )
    db.commit()

    # Trigger recovery email emulation!
    send_recovery_email(usuario.correo, usuario.nombre, token_str)

    return {
        "message": "Si el correo existe, se genero un token de recuperacion.",
        "token": token_str,
    }


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    registro = db.scalar(
        select(TokenRecuperacion).where(
            TokenRecuperacion.token == payload.token,
            TokenRecuperacion.usado.is_(False),
        )
    )

    if registro is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token invalido o ya fue utilizado.",
        )

    ahora = datetime.now(timezone.utc).replace(tzinfo=None)
    if ahora > registro.expira_en:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El token ha expirado. Solicita uno nuevo.",
        )

    usuario = db.get(Usuario, registro.usuario_id)
    if usuario is None or not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado.",
        )

    usuario.hash_contrasena = pwd_context.hash(payload.nueva_contrasena)
    registro.usado = True
    db.commit()

    return {"message": "Contrasena actualizada correctamente."}
