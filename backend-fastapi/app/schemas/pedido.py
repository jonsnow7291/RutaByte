from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class DetalleItemCreate(BaseModel):
    producto_id: int
    cantidad: int = Field(ge=1)
    notas: str | None = Field(default=None, max_length=150)


class PedidoCreate(BaseModel):
    mesa_id: int
    items: list[DetalleItemCreate] = Field(min_length=1)


class DetalleItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    producto_id: int
    cantidad: int
    precio_unitario: Decimal
    costo_unitario: Decimal
    notas: str | None


class PedidoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mesa_id: int
    usuario_id: int
    estado: str
    creado_en: datetime
    detalles: list[DetalleItemResponse] = []


class PedidoListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mesa_id: int
    usuario_id: int
    estado: str
    creado_en: datetime
