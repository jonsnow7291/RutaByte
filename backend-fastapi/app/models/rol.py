from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.usuario import Usuario


class Rol(Base):
    __tablename__ = "ROLES"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="rol")

