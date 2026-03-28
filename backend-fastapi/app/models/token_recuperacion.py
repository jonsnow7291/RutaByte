from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TokenRecuperacion(Base):
    __tablename__ = "TOKENS_RECUPERACION"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("USUARIOS.id"), nullable=False)
    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    usado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expira_en: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)
