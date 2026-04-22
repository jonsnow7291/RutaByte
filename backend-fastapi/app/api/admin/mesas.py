from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.mesa import MesaCreate, MesaResponse, MesaUpdate
from app.crud.mesa import (
    crear_mesa,
    obtener_mesas,
    obtener_mesas_por_sede,
    actualizar_mesa,
    eliminar_mesa
)

router = APIRouter(prefix="/admin/mesas", tags=["Mesas"])


@router.post("/", response_model=MesaResponse)
def crear(db: Session = Depends(get_db), mesa: MesaCreate = None):
    return crear_mesa(db, mesa)


@router.get("/", response_model=list[MesaResponse])
def listar(db: Session = Depends(get_db)):
    return obtener_mesas(db)


@router.get("/sede/{sede_id}", response_model=list[MesaResponse])
def listar_por_sede(sede_id: int, db: Session = Depends(get_db)):
    return obtener_mesas_por_sede(db, sede_id)


@router.put("/{mesa_id}", response_model=MesaResponse)
def actualizar(mesa_id: int, datos: MesaUpdate, db: Session = Depends(get_db)):
    mesa = actualizar_mesa(db, mesa_id, datos)
    if not mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    return mesa


@router.delete("/{mesa_id}")
def eliminar(mesa_id: int, db: Session = Depends(get_db)):
    mesa = eliminar_mesa(db, mesa_id)
    if not mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    return {"message": "Mesa desactivada"}