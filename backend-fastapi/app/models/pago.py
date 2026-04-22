from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Pago(Base):
    __tablename__ = "PAGOS"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    pedido_id: Mapped[int] = mapped_column(ForeignKey("PEDIDOS.id"), unique=True, nullable=False)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("USUARIOS.id"), nullable=False)
    metodo_pago: Mapped[str] = mapped_column(String(20), nullable=False)
    monto_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    monto_efectivo: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    monto_tarjeta: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    referencia: Mapped[str | None] = mapped_column(String(100), nullable=True)
    comprobante: Mapped[str | None] = mapped_column(Text, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)

    pedido = relationship("Pedido")
    usuario = relationship("Usuario")
