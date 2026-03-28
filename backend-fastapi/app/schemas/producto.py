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
    nombre: str = Field(min_length=2, max_length=150)
    descripcion: str | None = Field(default=None, max_length=2000)
    precio: Decimal = Field(ge=0)
    url_imagen: str | None = Field(default=None, max_length=500)


class ProductoUpdate(BaseModel):
    categoria_id: int | None = None
    nombre: str | None = Field(default=None, min_length=2, max_length=150)
    descripcion: str | None = Field(default=None, max_length=2000)
    precio: Decimal | None = Field(default=None, ge=0)
    url_imagen: str | None = Field(default=None, max_length=500)


class ProductoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    categoria_id: int
    nombre: str
    descripcion: str | None
    precio: Decimal
    url_imagen: str | None
    activo: bool
    creado_en: datetime
