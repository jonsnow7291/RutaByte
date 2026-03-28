from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RegistroAuditoria(Base):
    __tablename__ = "REGISTROS_AUDITORIA"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("USUARIOS.id", ondelete="SET NULL"), nullable=True)
    tipo_evento: Mapped[str] = mapped_column(String(50), nullable=False)
    direccion_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)
