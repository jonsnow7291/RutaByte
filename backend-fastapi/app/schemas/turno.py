from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class TurnoCajaApertura(BaseModel):
    monto_apertura: Decimal = Field(ge=0)


class TurnoCajaCierre(BaseModel):
    monto_cierre_real: Decimal = Field(ge=0)
    justificacion: str | None = Field(default=None, max_length=255)


class TurnoCajaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: int
    sede_id: int
    fecha_apertura: datetime
    fecha_cierre: datetime | None
    monto_apertura: Decimal
    monto_cierre_real: Decimal | None
    monto_cierre_esperado: Decimal | None
    estado: str
    justificacion: str | None
