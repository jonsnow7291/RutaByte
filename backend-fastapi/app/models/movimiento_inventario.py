from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MovimientoInventario(Base):
    __tablename__ = "MOVIMIENTOS_INVENTARIO"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    inventario_id: Mapped[int] = mapped_column(ForeignKey("INVENTARIO.id", ondelete="CASCADE"), nullable=False)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("USUARIOS.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    stock_anterior: Mapped[int] = mapped_column(Integer, nullable=False)
    stock_nuevo: Mapped[int] = mapped_column(Integer, nullable=False)
    motivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)

    inventario = relationship("Inventario", back_populates="movimientos")
    usuario = relationship("Usuario")
