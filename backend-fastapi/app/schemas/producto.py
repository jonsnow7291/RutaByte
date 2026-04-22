from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CategoriaCreate(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)


class CategoriaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    activa: bool


class ProductoCreate(BaseModel):
    categoria_id: int
    codigo: str | None = Field(default=None, min_length=1, max_length=50)
    nombre: str = Field(min_length=2, max_length=150)
    descripcion: str | None = Field(default=None, max_length=2000)
    precio: Decimal = Field(ge=0)
    costo_compra: Decimal = Field(default=0, ge=0)
    url_imagen: str | None = Field(default=None, max_length=500)


class ProductoUpdate(BaseModel):
    categoria_id: int | None = None
    codigo: str | None = Field(default=None, min_length=1, max_length=50)
    nombre: str | None = Field(default=None, min_length=2, max_length=150)
    descripcion: str | None = Field(default=None, max_length=2000)
    precio: Decimal | None = Field(default=None, ge=0)
    costo_compra: Decimal | None = Field(default=None, ge=0)
    url_imagen: str | None = Field(default=None, max_length=500)


class ProductoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    categoria_id: int
    codigo: str | None
    nombre: str
    descripcion: str | None
    precio: Decimal
    costo_compra: Decimal
    url_imagen: str | None
    activo: bool
    creado_en: datetime
