from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_admin
from app.db.session import get_db
from app.models.mesa import Mesa
from app.models.sede import Sede
from app.models.usuario import Usuario
from app.schemas.sede import SedeCreate, SedeResponse


router = APIRouter(
    prefix="/admin/sedes",
    tags=["admin-sedes"],
    dependencies=[Depends(get_current_admin)],
)


@router.post("", response_model=SedeResponse, status_code=status.HTTP_201_CREATED)
def crear_sede(payload: SedeCreate, db: Session = Depends(get_db)) -> Sede:
    sede = Sede(**payload.model_dump())
    db.add(sede)
    db.commit()
    db.refresh(sede)
    return sede


@router.get("", response_model=list[SedeResponse])
def listar_sedes(db: Session = Depends(get_db)) -> list[Sede]:
    stmt = select(Sede).where(Sede.activa.is_(True)).order_by(Sede.nombre.asc())
    return list(db.scalars(stmt).all())


@router.delete("/{sede_id}")
def desactivar_sede(sede_id: int, db: Session = Depends(get_db)) -> dict[str, str | int]:
    sede = db.get(Sede, sede_id)
    if sede is None or not sede.activa:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sede no encontrada")

    mesas_activas = db.scalar(
        select(func.count())
        .select_from(Mesa)
        .where(Mesa.sede_id == sede_id, Mesa.activa.is_(True))
    )
    usuarios_asignados = db.scalar(
        select(func.count())
        .select_from(Usuario)
        .where(Usuario.sede_id == sede_id)
    )

    if (mesas_activas or 0) > 0 or (usuarios_asignados or 0) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede desactivar la sede porque tiene mesas activas o usuarios asignados",
        )

    sede.activa = False
    db.commit()
    db.refresh(sede)
    return {"message": "Sede desactivada correctamente", "id": sede.id}

