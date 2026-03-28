from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.rol import Rol
    from app.models.sede import Sede


class Usuario(Base):
    __tablename__ = "USUARIOS"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rol_id: Mapped[int] = mapped_column(ForeignKey("ROLES.id"), nullable=False)
    sede_id: Mapped[int | None] = mapped_column(ForeignKey("SEDES.id"), nullable=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    correo: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    hash_contrasena: Mapped[str] = mapped_column(String(255), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)

    rol: Mapped["Rol"] = relationship(back_populates="usuarios")
    sede: Mapped["Sede | None"] = relationship(back_populates="usuarios")

