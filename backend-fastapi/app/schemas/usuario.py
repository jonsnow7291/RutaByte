from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


import re
from pydantic import field_validator

class UsuarioCreate(BaseModel):
    nombre: str = Field(min_length=2, max_length=150)
    correo: EmailStr = Field(max_length=150)
    contrasena: str = Field(min_length=8, max_length=128)
    rol_id: int
    sede_id: int | None = None

    @field_validator("contrasena")
    @classmethod
    def check_password_complexity(cls, value: str) -> str:
        if not re.search(r"[A-Z]", value):
            raise ValueError("La contrasena debe contener al menos una letra mayuscula")
        if not re.search(r"[a-z]", value):
            raise ValueError("La contrasena debe contener al menos una letra minuscula")
        if not re.search(r"\d", value):
            raise ValueError("La contrasena debe contener al menos un numero")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise ValueError("La contrasena debe contener al menos un caracter especial")
        return value


class UsuarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    correo: str
    rol_id: int
    sede_id: int | None
    activo: bool
    creado_en: datetime
