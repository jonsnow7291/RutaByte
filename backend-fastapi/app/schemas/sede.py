from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SedeBase(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    direccion: str | None = Field(default=None, max_length=255)
    ciudad: str | None = Field(default=None, max_length=100)


class SedeCreate(SedeBase):
    pass


class SedeResponse(SedeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    activa: bool
    creado_en: datetime

