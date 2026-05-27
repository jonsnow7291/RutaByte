from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_cajero
from app.db.session import get_db
from app.models.turno_caja import TurnoCaja
from app.models.pago import Pago
from app.models.mesa import Mesa
from app.schemas.turno import TurnoCajaApertura, TurnoCajaCierre, TurnoCajaResponse
from app.schemas.pago import PagoResponse

router = APIRouter(prefix="/cajero/turnos", tags=["cajero-turnos"])


@router.post("/apertura", response_model=TurnoCajaResponse, status_code=status.HTTP_201_CREATED)
def abrir_turno(
    payload: TurnoCajaApertura,
    current_user: dict = Depends(get_current_cajero),
    db: Session = Depends(get_db),
) -> TurnoCaja:
    usuario_id = int(current_user.get("usuario_id"))
    sede_id = current_user.get("sede_id")

    if sede_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario no tiene una sede asignada",
        )

    # Check if there is an active shift
    stmt = select(TurnoCaja).where(
        TurnoCaja.usuario_id == usuario_id,
        TurnoCaja.sede_id == int(sede_id),
        TurnoCaja.estado == "ABIERTO",
    )
    activo = db.scalar(stmt)
    if activo is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un turno de caja activo para este usuario en esta sede",
        )

    turno = TurnoCaja(
        usuario_id=usuario_id,
        sede_id=int(sede_id),
        monto_apertura=payload.monto_apertura,
        estado="ABIERTO",
        fecha_apertura=datetime.now(),
    )
    db.add(turno)
    db.commit()
    db.refresh(turno)
    return turno


@router.post("/cierre", response_model=TurnoCajaResponse)
def cerrar_turno(
    payload: TurnoCajaCierre,
    current_user: dict = Depends(get_current_cajero),
    db: Session = Depends(get_db),
) -> TurnoCaja:
    usuario_id = int(current_user.get("usuario_id"))
    sede_id = current_user.get("sede_id")

    if sede_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario no tiene una sede asignada",
        )

    # Find the active shift
    stmt = select(TurnoCaja).where(
        TurnoCaja.usuario_id == usuario_id,
        TurnoCaja.sede_id == int(sede_id),
        TurnoCaja.estado == "ABIERTO",
    )
    turno = db.scalar(stmt)
    if turno is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró un turno activo para cerrar",
        )

    # Calculate expected cash in cashier
    # sum of Pago.monto_efectivo since shift open
    query = select(func.sum(Pago.monto_efectivo)).where(
        Pago.usuario_id == usuario_id,
        Pago.creado_en >= turno.fecha_apertura,
    )
    total_efectivo = db.scalar(query) or Decimal("0")
    monto_cierre_esperado = turno.monto_apertura + total_efectivo

    monto_cierre_real = payload.monto_cierre_real
    justificacion = payload.justificacion

    # If there is a discrepancy, check if justification is provided
    if abs(monto_cierre_real - monto_cierre_esperado) > Decimal("0.01"):
        if not justificacion or not justificacion.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Se requiere una justificación por descuadre de caja",
            )

    turno.fecha_cierre = datetime.now()
    turno.monto_cierre_real = monto_cierre_real
    turno.monto_cierre_esperado = monto_cierre_esperado
    turno.estado = "CERRADO"
    turno.justificacion = justificacion

    db.commit()
    db.refresh(turno)
    return turno


@router.get("/activo", response_model=TurnoCajaResponse)
def obtener_turno_activo(
    current_user: dict = Depends(get_current_cajero),
    db: Session = Depends(get_db),
) -> TurnoCaja:
    role_id = int(current_user.get("rol_id", current_user.get("role_id")))
    usuario_id = int(current_user.get("usuario_id"))
    sede_id = current_user.get("sede_id")

    if role_id == 1 and sede_id is None:
        dummy = TurnoCaja(id=0, usuario_id=usuario_id, sede_id=0, monto_apertura=0, estado="ADMIN_BYPASS", fecha_apertura=datetime.now())
        dummy.fecha_cierre = None
        dummy.monto_cierre_real = None
        dummy.monto_cierre_esperado = None
        dummy.justificacion = None
        return dummy

    if sede_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario no tiene una sede asignada",
        )

    stmt = select(TurnoCaja).where(
        TurnoCaja.usuario_id == usuario_id,
        TurnoCaja.sede_id == int(sede_id),
        TurnoCaja.estado == "ABIERTO",
    )
    turno = db.scalar(stmt)
    if turno is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay un turno de caja activo",
        )
    return turno


@router.get("/transacciones", response_model=list[PagoResponse])
def obtener_transacciones_turno_activo(
    current_user: dict = Depends(get_current_cajero),
    db: Session = Depends(get_db),
) -> list[dict]:
    usuario_id = int(current_user.get("usuario_id"))
    sede_id = current_user.get("sede_id")

    if sede_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario no tiene una sede asignada",
        )

    # Find the active shift
    stmt = select(TurnoCaja).where(
        TurnoCaja.usuario_id == usuario_id,
        TurnoCaja.sede_id == int(sede_id),
        TurnoCaja.estado == "ABIERTO",
    )
    turno = db.scalar(stmt)
    if turno is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay un turno de caja activo",
        )

    # Fetch payments registered since shift open
    query = (
        select(Pago)
        .where(
            Pago.usuario_id == usuario_id,
            Pago.creado_en >= turno.fecha_apertura,
        )
        .order_by(Pago.creado_en.desc())
    )
    pagos = list(db.scalars(query).all())

    resultados = []
    for pago in pagos:
        pedido = pago.pedido
        mesa = db.get(Mesa, pedido.mesa_id) if pedido else None
        resultados.append({
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
        })
    return resultados
