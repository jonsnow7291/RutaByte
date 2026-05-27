from __future__ import annotations

from decimal import Decimal
import asyncio

from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload

from app.dependencies.auth import get_current_cajero
from app.db.session import get_db
from app.models.mesa import Mesa
from app.models.pago import Pago
from app.models.pedido import Pedido
from app.models.sede import Sede
from app.models.usuario import Usuario
from app.models.turno_caja import TurnoCaja
from app.schemas.pago import PagoCreate, PagoResponse, PedidoPendienteCobroResponse
from app.schemas.pedido import PedidoDescuentoApply, PedidoResponse
from app.services.inventario_service import descontar_inventario
from app.core.notifications import notification_manager

router = APIRouter(prefix="/cajero/pagos", tags=["cajero-pagos"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def _safe_broadcast(message: dict) -> None:
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(notification_manager.broadcast(message))
    except RuntimeError:
        pass


def _pedido_total(pedido: Pedido) -> Decimal:
    total = Decimal("0")
    for detalle in pedido.detalles:
        if not detalle.cancelado:
            iva_rate = Decimal("0")
            if detalle.producto:
                iva_rate = Decimal(str(detalle.producto.impuesto_iva or 0)) / Decimal("100")
            item_base = Decimal(detalle.cantidad) * detalle.precio_unitario
            total += item_base + (item_base * iva_rate)
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


def _sede_nombre(db: Session, sede_id: int | None) -> str | None:
    if sede_id is None:
        return None
    sede = db.get(Sede, sede_id)
    return sede.nombre if sede else None


def _serializar_pago(db: Session, pago: Pago) -> dict:
    pedido = pago.pedido
    mesa = _mesa_de_pedido(db, pedido)
    return {
        "id": pago.id,
        "pedido_id": pago.pedido_id,
        "usuario_id": pago.usuario_id,
        "metodo_pago": pago.metodo_pago,
        "monto_total": pago.monto_total,
        "subtotal_base": pago.subtotal_base,
        "impuesto_total": pago.impuesto_total,
        "monto_efectivo": pago.monto_efectivo,
        "monto_tarjeta": pago.monto_tarjeta,
        "referencia": pago.referencia,
        "comprobante": pago.comprobante,
        "creado_en": pago.creado_en,
        "mesa_id": mesa.id if mesa else None,
        "mesa_nombre": mesa.identificador_mesa if mesa else None,
        "sede_id": mesa.sede_id if mesa else None,
        "sede_nombre": _sede_nombre(db, mesa.sede_id if mesa else None),
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
        total = _pedido_total(pedido)
        final_total = max(total - pedido.descuento, Decimal("0"))
        resultados.append(
            PedidoPendienteCobroResponse(
                id=pedido.id,
                mesa_id=pedido.mesa_id,
                mesa_nombre=mesa.identificador_mesa if mesa else None,
                sede_id=mesa.sede_id if mesa else None,
                sede_nombre=_sede_nombre(db, mesa.sede_id if mesa else None),
                usuario_id=pedido.usuario_id,
                estado=pedido.estado,
                total=final_total,
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
    usuario_id = int(current_user.get("usuario_id"))
    role_id = int(current_user.get("rol_id", current_user.get("role_id")))
    sede_id = current_user.get("sede_id")

    stmt = select(Pedido).options(selectinload(Pedido.detalles)).where(Pedido.id == payload.pedido_id)
    pedido = db.scalar(stmt)
    if pedido is None:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    _pedido_permitido(pedido, current_user, db)

    if role_id != 1:
        if sede_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El usuario no tiene una sede asignada",
            )

        # Enforce shift restriction: Cajero must have an open shift in this sede
        shift_stmt = select(TurnoCaja).where(
            TurnoCaja.usuario_id == usuario_id,
            TurnoCaja.sede_id == int(sede_id),
            TurnoCaja.estado == "ABIERTO",
        )
        shift = db.scalar(shift_stmt)
        if shift is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pueden registrar pagos sin un turno de caja abierto",
            )
    else:
        mesa = db.get(Mesa, pedido.mesa_id)
        sede_id = mesa.sede_id if mesa else 0

    if pedido.estado == "PAGADO":
        raise HTTPException(status_code=400, detail="El pedido ya fue pagado")
    if pedido.estado != "ENTREGADO":
        raise HTTPException(status_code=400, detail="Solo se pueden cobrar pedidos entregados")

    existente = db.scalar(select(Pago).where(Pago.pedido_id == pedido.id))
    if existente is not None:
        raise HTTPException(status_code=409, detail="Ya existe un pago registrado para este pedido")

    items_total = _pedido_total(pedido)
    total = max(items_total - pedido.descuento, Decimal("0"))

    monto_efectivo = payload.monto_efectivo or Decimal("0")
    monto_tarjeta = payload.monto_tarjeta or Decimal("0")

    if payload.metodo_pago == "EFECTIVO" and monto_efectivo != total:
        raise HTTPException(status_code=400, detail="El monto en efectivo debe ser igual al total")
    if payload.metodo_pago == "TARJETA" and monto_tarjeta != total:
        raise HTTPException(status_code=400, detail="El monto en tarjeta debe ser igual al total")
    if payload.metodo_pago == "MIXTO" and (monto_efectivo + monto_tarjeta) != total:
        raise HTTPException(status_code=400, detail="La suma de efectivo y tarjeta debe ser igual al total")

    try:
        # Atomic stock deduction and tax breakdown calculations
        total_base_items = Decimal("0")
        total_iva_items = Decimal("0")

        for detalle in pedido.detalles:
            if not detalle.cancelado:
                iva_rate = Decimal("0")
                if detalle.producto:
                    iva_rate = Decimal(str(detalle.producto.impuesto_iva or 0)) / Decimal("100")

                detalle.precio_base = detalle.precio_unitario
                detalle.impuesto_iva_total = detalle.precio_unitario * iva_rate * Decimal(detalle.cantidad)

                total_base_items += detalle.precio_base * Decimal(detalle.cantidad)
                total_iva_items += detalle.impuesto_iva_total

                descontar_inventario(
                    db=db,
                    sede_id=int(sede_id),
                    producto_id=detalle.producto_id,
                    cantidad=detalle.cantidad,
                    usuario_id=usuario_id,
                )

        items_total = total_base_items + total_iva_items
        if items_total > 0:
            ratio = total / items_total
        else:
            ratio = Decimal("0")

        subtotal_base = total_base_items * ratio
        impuesto_total = total_iva_items * ratio

        pago = Pago(
            pedido_id=pedido.id,
            usuario_id=usuario_id,
            metodo_pago=payload.metodo_pago,
            monto_total=total,
            subtotal_base=subtotal_base,
            impuesto_total=impuesto_total,
            monto_efectivo=None if payload.metodo_pago == "TARJETA" else monto_efectivo,
            monto_tarjeta=None if payload.metodo_pago == "EFECTIVO" else monto_tarjeta,
            referencia=payload.referencia,
            comprobante=f"COMPROBANTE #{pedido.id} - Base: {subtotal_base} - Impuesto: {impuesto_total} - Total: {total}",
        )
        pedido.estado = "PAGADO"

        mesa = db.get(Mesa, pedido.mesa_id)
        if mesa is not None:
            mesa.estado = "LIBRE"

        db.add(pago)
        db.commit()
        db.refresh(pago)

        # Broadcast payment success WebSocket notification!
        _safe_broadcast(
            {
                "evento": "PAGO_PROCESADO",
                "pedido_id": pedido.id,
                "total": float(total),
                "mensaje": f"Pago de #{pedido.id} por {total} procesado exitosamente",
            }
        )

        return _serializar_pago(db, pago)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al procesar el pago") from exc


@router.post("/{pedido_id}/descuento", response_model=PedidoResponse)
def aplicar_descuento(
    pedido_id: int,
    payload: PedidoDescuentoApply,
    current_user: dict = Depends(get_current_cajero),
    db: Session = Depends(get_db),
) -> Pedido:
    pedido = db.scalar(
        select(Pedido)
        .options(selectinload(Pedido.detalles))
        .where(Pedido.id == pedido_id)
    )
    if pedido is None:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    _pedido_permitido(pedido, current_user, db)

    if pedido.estado == "PAGADO":
        raise HTTPException(status_code=400, detail="El pedido ya está pagado")

    # Authorizing Admin check
    admin = db.scalar(
        select(Usuario).where(
            func.lower(Usuario.correo) == payload.admin_username.strip().lower(),
            Usuario.activo.is_(True),
        )
    )
    if admin is None or admin.rol_id != 1:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas o el usuario no posee rol de Administrador",
        )

    # Verify password
    if not pwd_context.verify(payload.admin_password, admin.hash_contrasena):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Contraseña de administrador incorrecta",
        )

    # Calculate discount
    items_total = _pedido_total(pedido)
    if payload.tipo_descuento == "PORCENTAJE":
        if payload.descuento_valor < 0 or payload.descuento_valor > 100:
            raise HTTPException(status_code=400, detail="El porcentaje debe estar entre 0 y 100")
        descuento = items_total * (payload.descuento_valor / Decimal("100"))
    else:
        descuento = payload.descuento_valor

    # Cap discount
    descuento = min(descuento, items_total)
    descuento = max(descuento, Decimal("0"))

    pedido.descuento = descuento
    pedido.tipo_descuento = payload.tipo_descuento
    pedido.descuento_valor = payload.descuento_valor
    pedido.descuento_autorizado_por = admin.id

    db.commit()
    db.refresh(pedido)
    return pedido
