from __future__ import annotations

import csv
import io
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.dependencies.auth import get_current_cajero
from app.db.session import get_db
from app.models.mesa import Mesa
from app.models.pago import Pago
from app.models.pedido import Pedido
from app.models.sede import Sede
from app.schemas.reporte import ReporteVentaItem


router = APIRouter(prefix="/reportes", tags=["reportes"])


def _role_id(current_user: dict) -> int:
    return int(current_user.get("rol_id", current_user.get("role_id")))


def _resolve_sedes(current_user: dict, sede_id: int | None) -> set[int]:
    role_id = _role_id(current_user)
    if role_id == 1:
        if sede_id is None:
            return set()
        return {sede_id}

    user_sede_id = current_user.get("sede_id")
    if user_sede_id is None:
        raise HTTPException(status_code=400, detail="El usuario no tiene sede asignada")
    return {int(user_sede_id)}


def _construir_reporte(db: Session, current_user: dict, fecha_inicio: datetime, fecha_fin: datetime, sede_id: int | None = None) -> list[ReporteVentaItem]:
    sedes_filtradas = _resolve_sedes(current_user, sede_id)
    stmt = (
        select(Pago)
        .options(
            selectinload(Pago.pedido).selectinload(Pedido.detalles),
            selectinload(Pago.pedido).selectinload(Pedido.mesa),
        )
        .where(Pago.creado_en >= fecha_inicio, Pago.creado_en <= fecha_fin)
        .order_by(Pago.creado_en.asc())
    )
    pagos = list(db.scalars(stmt).all())

    sedes_cache: dict[int, Sede | None] = {}
    filas: list[ReporteVentaItem] = []
    for pago in pagos:
        pedido = pago.pedido
        if pedido is None:
            continue
        mesa = pedido.mesa or db.get(Mesa, pedido.mesa_id)
        if mesa is None:
            continue
        if sedes_filtradas and mesa.sede_id not in sedes_filtradas:
            continue

        if mesa.sede_id not in sedes_cache:
            sedes_cache[mesa.sede_id] = db.get(Sede, mesa.sede_id)
        sede = sedes_cache[mesa.sede_id]
        sede_nombre = sede.nombre if sede else f"Sede {mesa.sede_id}"

        for detalle in pedido.detalles:
            venta_total = Decimal(detalle.cantidad) * detalle.precio_unitario
            costo_total = Decimal(detalle.cantidad) * detalle.costo_unitario
            filas.append(
                ReporteVentaItem(
                    fecha=pago.creado_en,
                    sede_id=mesa.sede_id,
                    sede=sede_nombre,
                    codigo_producto=detalle.producto.codigo or str(detalle.producto_id),
                    producto=detalle.producto.nombre,
                    unidades_vendidas=detalle.cantidad,
                    precio_compra=detalle.costo_unitario,
                    precio_venta=detalle.precio_unitario,
                    venta_total=venta_total,
                    costo_total=costo_total,
                    ganancia=venta_total - costo_total,
                )
            )
    return filas


@router.get("/ventas", response_model=list[ReporteVentaItem])
def reporte_ventas(
    fecha_inicio: datetime = Query(...),
    fecha_fin: datetime = Query(...),
    sede_id: int | None = None,
    current_user: dict = Depends(get_current_cajero),
    db: Session = Depends(get_db),
) -> list[ReporteVentaItem]:
    return _construir_reporte(db, current_user, fecha_inicio, fecha_fin, sede_id=sede_id)


@router.get("/ventas/export/csv")
def exportar_reporte_ventas_csv(
    fecha_inicio: datetime = Query(...),
    fecha_fin: datetime = Query(...),
    sede_id: int | None = None,
    current_user: dict = Depends(get_current_cajero),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    filas = _construir_reporte(db, current_user, fecha_inicio, fecha_fin, sede_id=sede_id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "fecha",
        "sede_id",
        "sede",
        "codigo_producto",
        "producto",
        "unidades_vendidas",
        "precio_compra",
        "precio_venta",
        "venta_total",
        "costo_total",
        "ganancia",
    ])
    for fila in filas:
        writer.writerow([
            fila.fecha.isoformat(),
            fila.sede_id,
            fila.sede,
            fila.codigo_producto,
            fila.producto,
            fila.unidades_vendidas,
            str(fila.precio_compra),
            str(fila.precio_venta),
            str(fila.venta_total),
            str(fila.costo_total),
            str(fila.ganancia),
        ])

    output.seek(0)
    headers = {"Content-Disposition": 'attachment; filename="reporte_ventas.csv"'}
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers=headers)
