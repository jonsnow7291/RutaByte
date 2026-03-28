from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.producto import Producto


class Categoria(Base):
    __tablename__ = "CATEGORIAS"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    activa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    productos: Mapped[list["Producto"]] = relationship(back_populates="categoria")
