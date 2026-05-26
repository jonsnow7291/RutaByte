from __future__ import annotations

import csv
import io
import os
import asyncio
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.dependencies.auth import get_current_cajero
from app.db.session import get_db, SessionLocal
from app.models.mesa import Mesa
from app.models.pago import Pago
from app.models.pedido import Pedido
from app.models.sede import Sede
from app.models.inventario import Inventario
from app.models.producto import Producto
from app.schemas.reporte import ReporteVentaItem
from app.services.algoritmos_service import recursividad_simple_suma, recursividad_multiple_fibonacci
from app.core.notifications import notification_manager


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




@router.get("/ventas/resumen-recursivo")
def resumen_recursivo_ventas(
    fecha_inicio: datetime = Query(...),
    fecha_fin: datetime = Query(...),
    sede_id: int | None = None,
    current_user: dict = Depends(get_current_cajero),
    db: Session = Depends(get_db),
) -> dict:
    """Recursividad simple y multiple aplicada al reporte real de ventas.

    - Recursividad simple: suma de totales del reporte.
    - Recursividad multiple: Fibonacci como escenario academico de crecimiento
      sobre la cantidad de productos vendidos, limitado para evitar cargas altas.
    """
    filas = _construir_reporte(db, current_user, fecha_inicio, fecha_fin, sede_id=sede_id)
    ventas = [int(fila.venta_total) for fila in filas]
    costos = [int(fila.costo_total) for fila in filas]
    ganancias = [int(fila.ganancia) for fila in filas]
    nivel = min(len(filas), 20)

    return {
        "algoritmos_aplicados": ["Recursividad simple", "Recursividad multiple"],
        "filas": len(filas),
        "venta_total": recursividad_simple_suma(ventas),
        "costo_total": recursividad_simple_suma(costos),
        "ganancia_total": recursividad_simple_suma(ganancias),
        "escenario_fibonacci": recursividad_multiple_fibonacci(nivel),
    }


@router.get("/ventas-graficas")
def reporte_ventas_graficas(
    fecha_inicio: datetime = Query(...),
    fecha_fin: datetime = Query(...),
    sede_id: int | None = None,
    current_user: dict = Depends(get_current_cajero),
    db: Session = Depends(get_db),
) -> dict:
    """Datos agregados para graficas ejecutivas del reporte.

    Este endpoint reutiliza el reporte real de ventas y prepara la informacion
    para las graficas del frontend: ventas por dia, productos mas vendidos,
    ganancia por producto, ventas por sede y productos con stock bajo.
    """
    filas = _construir_reporte(db, current_user, fecha_inicio, fecha_fin, sede_id=sede_id)

    ventas_por_dia: dict[str, Decimal] = {}
    productos_top: dict[str, int] = {}
    ganancias: dict[str, Decimal] = {}
    ventas_sede: dict[str, Decimal] = {}

    for fila in filas:
        fecha_key = fila.fecha.date().isoformat()
        ventas_por_dia[fecha_key] = ventas_por_dia.get(fecha_key, Decimal("0")) + fila.venta_total
        productos_top[fila.producto] = productos_top.get(fila.producto, 0) + int(fila.unidades_vendidas)
        ganancias[fila.producto] = ganancias.get(fila.producto, Decimal("0")) + fila.ganancia
        ventas_sede[fila.sede] = ventas_sede.get(fila.sede, Decimal("0")) + fila.venta_total

    metodo_pago: dict[str, int] = {}
    stmt_pagos = (
        select(Pago)
        .options(selectinload(Pago.pedido).selectinload(Pedido.mesa))
        .where(Pago.creado_en >= fecha_inicio, Pago.creado_en <= fecha_fin)
    )
    for pago in db.scalars(stmt_pagos).all():
        pedido = pago.pedido
        mesa = pedido.mesa if pedido else None
        sedes_filtradas = _resolve_sedes(current_user, sede_id)
        if sedes_filtradas and mesa and mesa.sede_id not in sedes_filtradas:
            continue
        metodo = str(pago.metodo_pago or "SIN DEFINIR")
        metodo_pago[metodo] = metodo_pago.get(metodo, 0) + 1

    sedes_filtradas = _resolve_sedes(current_user, sede_id)
    stmt_inv = (
        select(Inventario)
        .options(selectinload(Inventario.producto), selectinload(Inventario.sede))
    )
    if sedes_filtradas:
        stmt_inv = stmt_inv.where(Inventario.sede_id.in_(sedes_filtradas))

    stock_bajo = []
    for inv in db.scalars(stmt_inv).all():
        producto = inv.producto
        umbral = int(getattr(producto, "umbral_minimo", inv.umbral_minimo or 0) or 0)
        if int(inv.stock or 0) <= umbral:
            stock_bajo.append({
                "producto": producto.nombre if producto else f"Producto {inv.producto_id}",
                "sede": inv.sede.nombre if inv.sede else f"Sede {inv.sede_id}",
                "stock": int(inv.stock or 0),
                "umbral": umbral,
            })

    return {
        "ventas_por_dia": [
            {"fecha": fecha, "total": float(total)}
            for fecha, total in sorted(ventas_por_dia.items())
        ],
        "productos_top": [
            {"producto": producto, "cantidad": cantidad}
            for producto, cantidad in sorted(productos_top.items(), key=lambda item: item[1], reverse=True)[:10]
        ],
        "ganancias": [
            {"producto": producto, "ganancia": float(total)}
            for producto, total in sorted(ganancias.items(), key=lambda item: item[1], reverse=True)[:10]
        ],
        "ventas_sede": [
            {"sede": sede, "total": float(total)}
            for sede, total in sorted(ventas_sede.items(), key=lambda item: item[1], reverse=True)
        ],
        "metodos_pago": [
            {"metodo": metodo, "cantidad": cantidad}
            for metodo, cantidad in sorted(metodo_pago.items(), key=lambda item: item[1], reverse=True)
        ],
        "stock_bajo": stock_bajo[:10],
    }


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


def _safe_broadcast(message: dict) -> None:
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(notification_manager.broadcast(message))
    except RuntimeError:
        pass


def generar_reporte_masivo_async(current_user: dict, fecha_inicio: datetime, fecha_fin: datetime, sede_id: int | None, file_name: str) -> None:
    db = SessionLocal()
    try:
        filas = _construir_reporte(db, current_user, fecha_inicio, fecha_fin, sede_id=sede_id)

        # Ensure static/reports exists
        os.makedirs("static/reports", exist_ok=True)
        file_path = os.path.join("static/reports", file_name)

        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "fecha", "sede_id", "sede", "codigo_producto", "producto",
                "unidades_vendidas", "precio_compra", "precio_venta",
                "venta_total", "costo_total", "ganancia"
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

        # Send WS notification when finished
        _safe_broadcast({
            "evento": "REPORTE_MASIVO_COMPLETO",
            "archivo_url": f"/static/reports/{file_name}",
            "mensaje": "El reporte global masivo ha sido generado exitosamente."
        })
    finally:
        db.close()


@router.post("/masivos")
def iniciar_reporte_masivo(
    background_tasks: BackgroundTasks,
    fecha_inicio: datetime = Query(...),
    fecha_fin: datetime = Query(...),
    sede_id: int | None = None,
    current_user: dict = Depends(get_current_cajero),
) -> dict:
    file_name = f"reporte_masivo_{int(datetime.now().timestamp())}.csv"
    background_tasks.add_task(
        generar_reporte_masivo_async,
        current_user,
        fecha_inicio,
        fecha_fin,
        sede_id,
        file_name
    )
    return {
        "status": "processing",
        "file_name": file_name,
        "message": "El reporte global masivo se está procesando en segundo plano.",
    }
