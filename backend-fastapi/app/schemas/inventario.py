from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class InventarioEntradaCreate(BaseModel):
    producto_id: int
    cantidad: int = Field(gt=0)
    motivo: str | None = Field(default=None, max_length=300)
    umbral_minimo: int | None = Field(default=None, ge=0)


class InventarioItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sede_id: int
    producto_id: int
    stock: int
    umbral_minimo: int
    actualizado_en: datetime


class MovimientoInventarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    inventario_id: int
    usuario_id: int
    tipo: str
    cantidad: int
    stock_anterior: int
    stock_nuevo: int
    motivo: str | None
    creado_en: datetime
