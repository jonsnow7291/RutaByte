from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.dependencies.auth import get_current_cajero
from app.db.session import get_db
from app.models.mesa import Mesa
from app.models.pago import Pago
from app.models.pedido import Pedido
from app.schemas.pago import PagoCreate, PagoResponse, PedidoPendienteCobroResponse


router = APIRouter(prefix="/cajero/pagos", tags=["cajero-pagos"])


def _pedido_total(pedido: Pedido) -> Decimal:
    total = Decimal("0")
    for detalle in pedido.detalles:
        total += Decimal(detalle.cantidad) * detalle.precio_unitario
    return total


def _pedido_permitido(pedido: Pedido, current_user: dict, db: Session) -> None:
    role_id = int(current_user.get("rol_id", current_user.get("role_id")))
    if role_id == 1:
        return

    user_sede_id = current_user.get("sede_id")
    mesa = db.get(Mesa, pedido.mesa_id)
    if mesa is None or user_sede_id is None or mesa.sede_id != int(user_sede_id):
        raise HTTPException(status_code=403, detail="No puede operar pedidos de otra sede")


def _mesa_de_pedido(db: Session, pedido: Pedido | None) -> Mesa | None:
    if pedido is None:
        return None
    if getattr(pedido, "mesa", None) is not None:
        return pedido.mesa
    return db.get(Mesa, pedido.mesa_id)


def _serializar_pago(db: Session, pago: Pago) -> dict:
    pedido = pago.pedido
    mesa = _mesa_de_pedido(db, pedido)
    return {
        "id": pago.id,
        "pedido_id": pago.pedido_id,
        "usuario_id": pago.usuario_id,
        "metodo_pago": pago.metodo_pago,
        "monto_total": pago.monto_total,
        "monto_efectivo": pago.monto_efectivo,
        "monto_tarjeta": pago.monto_tarjeta,
        "referencia": pago.referencia,
        "comprobante": pago.comprobante,
        "creado_en": pago.creado_en,
        "mesa_id": mesa.id if mesa else None,
        "mesa_nombre": mesa.identificador_mesa if mesa else None,
        "sede_id": mesa.sede_id if mesa else None,
    }


@router.get("/pendientes", response_model=list[PedidoPendienteCobroResponse])
def listar_pedidos_pendientes(
    current_user: dict = Depends(get_current_cajero),
    db: Session = Depends(get_db),
) -> list[PedidoPendienteCobroResponse]:
    stmt = select(Pedido).options(selectinload(Pedido.detalles)).where(Pedido.estado == "ENTREGADO").order_by(Pedido.creado_en.asc())
    pedidos = list(db.scalars(stmt).all())

    resultados: list[PedidoPendienteCobroResponse] = []
    for pedido in pedidos:
        try:
            _pedido_permitido(pedido, current_user, db)
        except HTTPException:
            continue
        mesa = _mesa_de_pedido(db, pedido)
        resultados.append(
            PedidoPendienteCobroResponse(
                id=pedido.id,
                mesa_id=pedido.mesa_id,
                mesa_nombre=mesa.identificador_mesa if mesa else None,
                sede_id=mesa.sede_id if mesa else None,
                usuario_id=pedido.usuario_id,
                estado=pedido.estado,
                total=_pedido_total(pedido),
            )
        )
    return resultados




@router.get("", response_model=list[PagoResponse])
def listar_pagos_recientes(
    current_user: dict = Depends(get_current_cajero),
    db: Session = Depends(get_db),
) -> list[dict]:
    stmt = (
        select(Pago)
        .options(selectinload(Pago.pedido))
        .order_by(Pago.creado_en.desc())
        .limit(50)
    )
    pagos = list(db.scalars(stmt).all())

    resultados: list[dict] = []
    for pago in pagos:
        if pago.pedido is None:
            continue
        try:
            _pedido_permitido(pago.pedido, current_user, db)
        except HTTPException:
            continue
        resultados.append(_serializar_pago(db, pago))
    return resultados


@router.post("", response_model=PagoResponse, status_code=status.HTTP_201_CREATED)
def procesar_pago(
    payload: PagoCreate,
    current_user: dict = Depends(get_current_cajero),
    db: Session = Depends(get_db),
) -> dict:
    stmt = select(Pedido).options(selectinload(Pedido.detalles)).where(Pedido.id == payload.pedido_id)
    pedido = db.scalar(stmt)
    if pedido is None:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    _pedido_permitido(pedido, current_user, db)

    if pedido.estado == "PAGADO":
        raise HTTPException(status_code=400, detail="El pedido ya fue pagado")
    if pedido.estado != "ENTREGADO":
        raise HTTPException(status_code=400, detail="Solo se pueden cobrar pedidos entregados")

    existente = db.scalar(select(Pago).where(Pago.pedido_id == pedido.id))
    if existente is not None:
        raise HTTPException(status_code=409, detail="Ya existe un pago registrado para este pedido")

    total = _pedido_total(pedido)
    monto_efectivo = payload.monto_efectivo or Decimal("0")
    monto_tarjeta = payload.monto_tarjeta or Decimal("0")
    if payload.metodo_pago == "EFECTIVO" and monto_efectivo != total:
        raise HTTPException(status_code=400, detail="El monto en efectivo debe ser igual al total")
    if payload.metodo_pago == "TARJETA" and monto_tarjeta != total:
        raise HTTPException(status_code=400, detail="El monto en tarjeta debe ser igual al total")
    if payload.metodo_pago == "MIXTO" and (monto_efectivo + monto_tarjeta) != total:
        raise HTTPException(status_code=400, detail="La suma de efectivo y tarjeta debe ser igual al total")

    usuario_id = int(current_user.get("usuario_id"))
    pago = Pago(
        pedido_id=pedido.id,
        usuario_id=usuario_id,
        metodo_pago=payload.metodo_pago,
        monto_total=total,
        monto_efectivo=None if payload.metodo_pago == "TARJETA" else monto_efectivo,
        monto_tarjeta=None if payload.metodo_pago == "EFECTIVO" else monto_tarjeta,
        referencia=payload.referencia,
        comprobante=f"COMPROBANTE #{pedido.id} - Total: {total}",
    )
    pedido.estado = "PAGADO"

    mesa = db.get(Mesa, pedido.mesa_id)
    if mesa is not None:
        mesa.estado = "LIBRE"

    db.add(pago)
    db.commit()
    db.refresh(pago)
    return _serializar_pago(db, pago)
