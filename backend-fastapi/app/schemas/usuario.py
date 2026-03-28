from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UsuarioCreate(BaseModel):
    nombre: str = Field(min_length=2, max_length=150)
    correo: EmailStr = Field(max_length=150)
    contrasena: str = Field(min_length=6, max_length=128)
    rol_id: int
    sede_id: int | None = None


class UsuarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    correo: str
    rol_id: int
    sede_id: int | None
    activo: bool
    creado_en: datetime
