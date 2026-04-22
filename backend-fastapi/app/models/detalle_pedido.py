from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.pedido import Pedido
    from app.models.producto import Producto


class DetallePedido(Base):
    __tablename__ = "DETALLE_PEDIDOS"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    pedido_id: Mapped[int] = mapped_column(ForeignKey("PEDIDOS.id", ondelete="CASCADE"), nullable=False)
    producto_id: Mapped[int] = mapped_column(ForeignKey("PRODUCTOS.id"), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    costo_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    notas: Mapped[str | None] = mapped_column(String(150), nullable=True)

    pedido: Mapped["Pedido"] = relationship(back_populates="detalles")
    producto: Mapped["Producto"] = relationship()
