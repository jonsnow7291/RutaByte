from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from decimal import Decimal
from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.detalle_pedido import DetallePedido
    from app.models.mesa import Mesa
    from app.models.usuario import Usuario


class Pedido(Base):
    __tablename__ = "PEDIDOS"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    mesa_id: Mapped[int] = mapped_column(ForeignKey("MESAS.id"), nullable=False)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("USUARIOS.id"), nullable=False)
    estado: Mapped[str] = mapped_column(String(50), default="EN_PREPARACION", nullable=False)
    descuento: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    tipo_descuento: Mapped[str | None] = mapped_column(String(20), nullable=True)
    descuento_valor: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    descuento_autorizado_por: Mapped[int | None] = mapped_column(ForeignKey("USUARIOS.id"), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)

    mesa: Mapped["Mesa"] = relationship()
    usuario: Mapped["Usuario"] = relationship(foreign_keys=[usuario_id])
    descuento_autorizado: Mapped["Usuario | None"] = relationship(foreign_keys=[descuento_autorizado_por])
    detalles: Mapped[list["DetallePedido"]] = relationship(back_populates="pedido", cascade="all, delete-orphan")
