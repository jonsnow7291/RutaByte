from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.sede import Sede


class Mesa(Base):
    __tablename__ = "MESAS"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sede_id: Mapped[int] = mapped_column(ForeignKey("SEDES.id"), nullable=False)
    identificador_mesa: Mapped[str] = mapped_column(String(50), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="LIBRE", nullable=False)
    activa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    sede: Mapped["Sede"] = relationship(back_populates="mesas")

