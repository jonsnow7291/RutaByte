from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
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
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)

    mesa: Mapped["Mesa"] = relationship()
    usuario: Mapped["Usuario"] = relationship()
    detalles: Mapped[list["DetallePedido"]] = relationship(back_populates="pedido", cascade="all, delete-orphan")
