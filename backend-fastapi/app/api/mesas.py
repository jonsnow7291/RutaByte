from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.mesa import Mesa
from app.models.sede import Sede
from app.schemas.mesa import MesaCreate, MesaUpdate, MesaResponse
from app.dependencies.auth import get_current_admin

router = APIRouter(prefix="/api/mesas", tags=["mesas"])

@router.get("", response_model=list[MesaResponse])
def listar_mesas(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin),
):
    return list(db.scalars(select(Mesa)).all())

@router.post("", response_model=MesaResponse, status_code=status.HTTP_201_CREATED)
def crear_mesa(
    payload: MesaCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin),
):
    sede = db.get(Sede, payload.sede_id)
    if sede is None:
        raise HTTPException(status_code=404, detail="Sede no encontrada")

    existente = db.scalar(
        select(Mesa).where(
            Mesa.sede_id == payload.sede_id,
            Mesa.identificador_mesa == payload.identificador_mesa
        )
    )
    if existente:
        raise HTTPException(
            status_code=400,
            detail="Ya existe una mesa con ese identificador en la sede",
        )

    mesa = Mesa(
        sede_id=payload.sede_id,
        identificador_mesa=payload.identificador_mesa,
        estado=payload.estado,
        activa=True,
    )
    db.add(mesa)
    db.commit()
    db.refresh(mesa)
    return mesa

@router.put("/{mesa_id}", response_model=MesaResponse)
def actualizar_mesa(
    mesa_id: int,
    payload: MesaUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin),
):
    mesa = db.get(Mesa, mesa_id)
    if mesa is None:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")

    existente = db.scalar(
        select(Mesa).where(
            Mesa.sede_id == payload.sede_id,
            Mesa.identificador_mesa == payload.identificador_mesa,
            Mesa.id != mesa_id,
        )
    )
    if existente:
        raise HTTPException(
            status_code=400,
            detail="Ya existe una mesa con ese identificador en la sede",
        )

    mesa.sede_id = payload.sede_id
    mesa.identificador_mesa = payload.identificador_mesa
    mesa.estado = payload.estado

    db.commit()
    db.refresh(mesa)
    return mesa

@router.delete("/{mesa_id}")
def desactivar_mesa(
    mesa_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin),
):
    mesa = db.get(Mesa, mesa_id)
    if mesa is None:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")

    mesa.activa = False
    db.commit()
    return {"message": "Mesa desactivada correctamente"}