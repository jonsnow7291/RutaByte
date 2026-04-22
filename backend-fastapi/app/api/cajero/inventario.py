from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_cajero
from app.db.session import get_db
from app.models.inventario import Inventario
from app.models.movimiento_inventario import MovimientoInventario
from app.models.producto import Producto
from app.models.sede import Sede
from app.schemas.inventario import InventarioEntradaCreate, InventarioItemResponse, MovimientoInventarioResponse
from app.services.inventario_service import registrar_entrada_inventario


router = APIRouter(prefix="/cajero/inventario", tags=["cajero-inventario"])


def _resolver_sede(current_user: dict, sede_id: int | None = None) -> int:
    role_id = int(current_user.get("rol_id", current_user.get("role_id")))
    user_sede_id = current_user.get("sede_id")

    if role_id == 1:
        if sede_id is None:
            raise HTTPException(status_code=400, detail="El administrador debe indicar la sede_id")
        return int(sede_id)

    if user_sede_id is None:
        raise HTTPException(status_code=400, detail="El usuario no tiene sede asignada")
    return int(user_sede_id)


@router.get("", response_model=list[InventarioItemResponse])
def listar_inventario(
    sede_id: int | None = None,
    current_user: dict = Depends(get_current_cajero),
    db: Session = Depends(get_db),
) -> list[Inventario]:
    resolved_sede_id = _resolver_sede(current_user, sede_id=sede_id)
    stmt = select(Inventario).where(Inventario.sede_id == resolved_sede_id).order_by(Inventario.producto_id.asc())
    return list(db.scalars(stmt).all())


@router.post("/entradas", response_model=InventarioItemResponse, status_code=status.HTTP_201_CREATED)
def crear_entrada_inventario(
    payload: InventarioEntradaCreate,
    sede_id: int | None = None,
    current_user: dict = Depends(get_current_cajero),
    db: Session = Depends(get_db),
) -> Inventario:
    resolved_sede_id = _resolver_sede(current_user, sede_id=sede_id)
    producto = db.get(Producto, payload.producto_id)
    if producto is None or not producto.activo:
        raise HTTPException(status_code=400, detail="Producto no valido")

    sede = db.get(Sede, resolved_sede_id)
    if sede is None or not sede.activa:
        raise HTTPException(status_code=400, detail="Sede no valida")

    usuario_id = int(current_user.get("usuario_id"))

    inventario = registrar_entrada_inventario(
        db=db,
        sede_id=resolved_sede_id,
        producto_id=payload.producto_id,
        cantidad=payload.cantidad,
        usuario_id=usuario_id,
        motivo=payload.motivo,
        umbral_minimo=payload.umbral_minimo,
    )
    db.commit()
    db.refresh(inventario)
    return inventario


@router.get("/movimientos", response_model=list[MovimientoInventarioResponse])
def listar_movimientos(
    sede_id: int | None = None,
    current_user: dict = Depends(get_current_cajero),
    db: Session = Depends(get_db),
) -> list[MovimientoInventario]:
    resolved_sede_id = _resolver_sede(current_user, sede_id=sede_id)
    stmt = (
        select(MovimientoInventario)
        .join(Inventario, Inventario.id == MovimientoInventario.inventario_id)
        .where(Inventario.sede_id == resolved_sede_id)
        .order_by(MovimientoInventario.creado_en.desc())
    )
    return list(db.scalars(stmt).all())
