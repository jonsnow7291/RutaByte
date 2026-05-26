from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.sede import Sede
    from app.models.usuario import Usuario


class TurnoCaja(Base):
    __tablename__ = "TURNOS_CAJA"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("USUARIOS.id"), nullable=False)
    sede_id: Mapped[int] = mapped_column(ForeignKey("SEDES.id"), nullable=False)
    fecha_apertura: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)
    fecha_cierre: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    monto_apertura: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    monto_cierre_real: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    monto_cierre_esperado: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), default="ABIERTO", nullable=False)  # 'ABIERTO', 'CERRADO'
    justificacion: Mapped[str | None] = mapped_column(String(255), nullable=True)

    usuario: Mapped["Usuario"] = relationship()
    sede: Mapped["Sede"] = relationship()
