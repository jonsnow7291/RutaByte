from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_admin
from app.db.session import get_db
from app.models.rol import Rol
from app.models.sede import Sede
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioResponse


router = APIRouter(
    prefix="/admin/usuarios",
    tags=["admin-usuarios"],
    dependencies=[Depends(get_current_admin)],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


@router.post("", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def crear_usuario(payload: UsuarioCreate, db: Session = Depends(get_db)) -> Usuario:
    rol = db.get(Rol, payload.rol_id)
    if rol is None or not rol.activo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rol no valido")

    if payload.sede_id is not None:
        sede = db.get(Sede, payload.sede_id)
        if sede is None or not sede.activa:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sede no valida")

    existe = db.scalar(
        select(Usuario).where(func.lower(Usuario.correo) == payload.correo.lower())
    )
    if existe:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un usuario con ese correo")

    usuario = Usuario(
        nombre=payload.nombre,
        correo=payload.correo,
        hash_contrasena=pwd_context.hash(payload.contrasena),
        rol_id=payload.rol_id,
        sede_id=payload.sede_id,
        activo=True,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.get("", response_model=list[UsuarioResponse])
def listar_usuarios(db: Session = Depends(get_db)) -> list[Usuario]:
    stmt = select(Usuario).where(Usuario.activo.is_(True)).order_by(Usuario.nombre.asc())
    return list(db.scalars(stmt).all())


@router.delete("/{usuario_id}")
def desactivar_usuario(usuario_id: int, db: Session = Depends(get_db)) -> dict[str, str | int]:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None or not usuario.activo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    usuario.activo = False
    db.commit()
    db.refresh(usuario)
    return {"message": "Usuario desactivado correctamente", "id": usuario.id}
