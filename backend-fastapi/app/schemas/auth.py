from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    correo: str = Field(min_length=5, max_length=150)
    contrasena: str = Field(min_length=1, max_length=255)

    @field_validator("correo")
    @classmethod
    def normalize_correo(cls, value: str) -> str:
        correo = value.strip().lower()
        if "@" not in correo or correo.startswith("@") or correo.endswith("@"):
            raise ValueError("El correo electronico no es valido")
        return correo


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    rol_id: int
    sede_id: int | None = None
    expires_in: int = 28_800


class RecuperarRequest(BaseModel):
    correo: str = Field(min_length=5, max_length=150)

    @field_validator("correo")
    @classmethod
    def normalize_correo(cls, value: str) -> str:
        correo = value.strip().lower()
        if "@" not in correo or correo.startswith("@") or correo.endswith("@"):
            raise ValueError("El correo electronico no es valido")
        return correo


import re

class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=1, max_length=64)
    nueva_contrasena: str = Field(min_length=8, max_length=128)

    @field_validator("nueva_contrasena")
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
