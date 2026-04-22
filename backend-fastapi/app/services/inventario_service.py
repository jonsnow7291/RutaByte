from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inventario import Inventario
from app.models.movimiento_inventario import MovimientoInventario


def obtener_inventario(db: Session, sede_id: int, producto_id: int) -> Inventario | None:
    stmt = select(Inventario).where(Inventario.sede_id == sede_id, Inventario.producto_id == producto_id)
    return db.scalar(stmt)


def registrar_entrada_inventario(
    db: Session,
    sede_id: int,
    producto_id: int,
    cantidad: int,
    usuario_id: int,
    motivo: str | None = None,
    umbral_minimo: int | None = None,
) -> Inventario:
    inventario = obtener_inventario(db, sede_id=sede_id, producto_id=producto_id)
    if inventario is None:
        inventario = Inventario(sede_id=sede_id, producto_id=producto_id, stock=0, umbral_minimo=umbral_minimo or 5)
        db.add(inventario)
        db.flush()
    elif umbral_minimo is not None:
        inventario.umbral_minimo = umbral_minimo

    stock_anterior = inventario.stock
    inventario.stock += cantidad
    movimiento = MovimientoInventario(
        inventario_id=inventario.id,
        usuario_id=usuario_id,
        tipo="ENTRADA",
        cantidad=cantidad,
        stock_anterior=stock_anterior,
        stock_nuevo=inventario.stock,
        motivo=motivo,
    )
    db.add(movimiento)
    db.flush()
    return inventario


def descontar_inventario(db: Session, sede_id: int, producto_id: int, cantidad: int, usuario_id: int) -> Inventario:
    inventario = obtener_inventario(db, sede_id=sede_id, producto_id=producto_id)

    if inventario is None:
        raise ValueError("No hay inventario registrado para este producto en la sede")

    if inventario.stock < cantidad:
        raise ValueError("Stock insuficiente")

    stock_anterior = inventario.stock
    inventario.stock -= cantidad

    movimiento = MovimientoInventario(
        inventario_id=inventario.id,
        usuario_id=usuario_id,
        tipo="SALIDA",
        cantidad=cantidad,
        stock_anterior=stock_anterior,
        stock_nuevo=inventario.stock,
        motivo="Descuento por creacion de pedido",
    )

    db.add(movimiento)
    db.flush()
    return inventario
