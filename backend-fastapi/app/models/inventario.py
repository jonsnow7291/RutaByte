from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Inventario(Base):
    __tablename__ = "INVENTARIO"
    __table_args__ = (UniqueConstraint("sede_id", "producto_id", name="uq_inventario_sede_producto"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sede_id: Mapped[int] = mapped_column(ForeignKey("SEDES.id"), nullable=False)
    producto_id: Mapped[int] = mapped_column(ForeignKey("PRODUCTOS.id"), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    umbral_minimo: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    sede = relationship("Sede")
    producto = relationship("Producto")
    movimientos = relationship("MovimientoInventario", back_populates="inventario", cascade="all, delete-orphan")
