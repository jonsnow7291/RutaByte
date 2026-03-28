from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.mesa import Mesa
    from app.models.usuario import Usuario


class Sede(Base):
    __tablename__ = "SEDES"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    direccion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ciudad: Mapped[str | None] = mapped_column(String(100), nullable=True)
    activa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="sede")
    mesas: Mapped[list["Mesa"]] = relationship(back_populates="sede")
