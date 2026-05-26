from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class RegistroAuditoriaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: int | None
    tipo_evento: str
    direccion_ip: str | None
    creado_en: datetime
