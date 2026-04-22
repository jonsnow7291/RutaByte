from pydantic import BaseModel
from typing import Optional

# 🔹 Crear
class MesaCreate(BaseModel):
    sede_id: int
    identificador_mesa: str


# 🔹 🔥 ACTUALIZAR (CLAVE)
class MesaUpdate(BaseModel):
    sede_id: Optional[int] = None
    identificador_mesa: Optional[str] = None
    estado: Optional[str] = None
    activa: Optional[bool] = None


# 🔹 Respuesta
class MesaResponse(BaseModel):
    id: int
    sede_id: int
    identificador_mesa: str
    estado: str
    activa: bool

    class Config:
        from_attributes = True