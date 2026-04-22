from pydantic import BaseModel

class MesaCreate(BaseModel):
    sede_id: int
    identificador_mesa: str
    estado: str

class MesaUpdate(BaseModel):
    sede_id: int
    identificador_mesa: str
    estado: str

class MesaResponse(BaseModel):
    id: int
    sede_id: int
    identificador_mesa: str
    estado: str
    activa: bool

    class Config:
        from_attributes = True