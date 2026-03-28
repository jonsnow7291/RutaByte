from __future__ import annotations

from dataclasses import dataclass

from passlib.context import CryptContext
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.rol import Rol
from app.models.sede import Sede
from app.models.usuario import Usuario


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


@dataclass(frozen=True)
class SeedUser:
    correo: str
    nombre: str
    password: str
    rol_nombre: str
    sede_nombre: str | None = None


DEFAULT_ROLES = ("ADMIN", "CAJERO", "MESERO")
DEFAULT_SEDE = {
    "nombre": "Sede Principal",
    "direccion": "Calle 1 # 1-1",
    "ciudad": "Bogota",
}
DEFAULT_USERS = (
    SeedUser(
        correo="admin@rutabyte.local",
        nombre="Administrador Principal",
        password="Admin123!",
        rol_nombre="ADMIN",
    ),
    SeedUser(
        correo="cajero@rutabyte.local",
        nombre="Cajero Principal",
        password="Cajero123!",
        rol_nombre="CAJERO",
        sede_nombre="Sede Principal",
    ),
    SeedUser(
        correo="mesero@rutabyte.local",
        nombre="Mesero Principal",
        password="Mesero123!",
        rol_nombre="MESERO",
        sede_nombre="Sede Principal",
    ),
)


def _get_role_by_name(db: Session, role_name: str) -> Rol | None:
    return db.scalar(select(Rol).where(func.lower(Rol.nombre) == role_name.lower()))


def _get_user_by_email(db: Session, correo: str) -> Usuario | None:
    return db.scalar(select(Usuario).where(func.lower(Usuario.correo) == correo.lower()))


def _get_sede_by_name(db: Session, sede_name: str) -> Sede | None:
    return db.scalar(select(Sede).where(func.lower(Sede.nombre) == sede_name.lower()))


def seed_initial_data(db: Session) -> None:
    roles_by_name: dict[str, Rol] = {}
    for role_name in DEFAULT_ROLES:
        rol = _get_role_by_name(db, role_name)
        if rol is None:
            rol = Rol(nombre=role_name, activo=True)
            db.add(rol)
            db.flush()
        roles_by_name[role_name] = rol

    sede_principal = _get_sede_by_name(db, DEFAULT_SEDE["nombre"])
    if sede_principal is None:
        sede_principal = Sede(**DEFAULT_SEDE)
        db.add(sede_principal)
        db.flush()

    for seed_user in DEFAULT_USERS:
        usuario = _get_user_by_email(db, seed_user.correo)
        if usuario is not None:
            continue

        db.add(
            Usuario(
                rol_id=roles_by_name[seed_user.rol_nombre].id,
                sede_id=None if seed_user.sede_nombre is None else sede_principal.id,
                nombre=seed_user.nombre,
                correo=seed_user.correo,
                hash_contrasena=pwd_context.hash(seed_user.password),
                activo=True,
            )
        )

    db.commit()
