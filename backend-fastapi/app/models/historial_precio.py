from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.producto import Producto
    from app.models.usuario import Usuario


class HistorialPrecio(Base):
    __tablename__ = "HISTORIAL_PRECIOS"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("PRODUCTOS.id", ondelete="CASCADE"), nullable=False)
    precio_anterior: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    precio_nuevo: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    cambiado_por: Mapped[int] = mapped_column(ForeignKey("USUARIOS.id"), nullable=False)
    cambiado_en: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)

    producto: Mapped["Producto"] = relationship()
    usuario: Mapped["Usuario"] = relationship()
