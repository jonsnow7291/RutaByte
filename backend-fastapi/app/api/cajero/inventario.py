from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.dependencies.auth import get_current_cajero
from app.db.session import get_db
from app.models.inventario import Inventario
from app.models.movimiento_inventario import MovimientoInventario
from app.models.producto import Producto
from app.models.sede import Sede
from app.schemas.inventario import InventarioEntradaCreate, InventarioItemResponse, MovimientoInventarioResponse, InventarioSalidaCreate
from app.services.inventario_service import registrar_entrada_inventario
from app.services.algoritmos_service import algoritmo_voraz_reabastecimiento, algoritmo_mochila


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
    stmt = select(Inventario).options(joinedload(Inventario.producto)).where(Inventario.sede_id == resolved_sede_id).order_by(Inventario.producto_id.asc())
    items = list(db.scalars(stmt).all())
    for item in items:
        if item.producto is not None:
            item.umbral_minimo = int(getattr(item.producto, "umbral_minimo", item.umbral_minimo) or 0)
    return items


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
        umbral_minimo=None,
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
        .options(joinedload(MovimientoInventario.inventario).joinedload(Inventario.producto))
        .join(Inventario, Inventario.id == MovimientoInventario.inventario_id)
        .where(Inventario.sede_id == resolved_sede_id)
        .order_by(MovimientoInventario.creado_en.desc())
    )
    return list(db.scalars(stmt).all())


def _productos_para_algoritmos(db: Session, sede_id: int) -> list[dict]:
    inventarios = list(
        db.scalars(
            select(Inventario)
            .options(joinedload(Inventario.producto))
            .where(Inventario.sede_id == sede_id)
            .order_by(Inventario.producto_id.asc())
        ).all()
    )

    resultado = []
    for item in inventarios:
        producto = item.producto
        if producto is None or not producto.activo:
            continue
        costo = float(producto.costo_compra or 0)
        precio = float(producto.precio or 0)
        resultado.append({
            "producto_id": item.producto_id,
            "codigo": producto.codigo or f"PROD-{item.producto_id}",
            "nombre": producto.nombre,
            "stock": item.stock,
            "umbral_minimo": int(getattr(producto, "umbral_minimo", item.umbral_minimo) or 0),
            "costo_compra": costo,
            "precio_venta": precio,
            "ganancia": max(precio - costo, 0),
            "valor": int(max(precio - costo, 0) + max(int(getattr(producto, "umbral_minimo", item.umbral_minimo) or 0) - item.stock, 0)),
        })
    return resultado


@router.get("/sugerencia-voraz")
def sugerencia_voraz_reabastecimiento(
    presupuesto: int,
    sede_id: int | None = None,
    current_user: dict = Depends(get_current_cajero),
    db: Session = Depends(get_db),
) -> dict:
    resolved_sede_id = _resolver_sede(current_user, sede_id=sede_id)
    productos = _productos_para_algoritmos(db, resolved_sede_id)
    resultado = algoritmo_voraz_reabastecimiento(productos, presupuesto)
    resultado["sede_id"] = resolved_sede_id
    return resultado


@router.get("/optimizar-compra")
def optimizar_compra_mochila(
    presupuesto: int,
    sede_id: int | None = None,
    current_user: dict = Depends(get_current_cajero),
    db: Session = Depends(get_db),
) -> dict:
    resolved_sede_id = _resolver_sede(current_user, sede_id=sede_id)
    productos = _productos_para_algoritmos(db, resolved_sede_id)
    resultado = algoritmo_mochila(productos, presupuesto)
    resultado["sede_id"] = resolved_sede_id
    return resultado


@router.post("/salidas", response_model=InventarioItemResponse, status_code=status.HTTP_201_CREATED)
def crear_salida_inventario(
    payload: InventarioSalidaCreate,
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
    inventario = db.scalar(
        select(Inventario).where(Inventario.sede_id == resolved_sede_id, Inventario.producto_id == payload.producto_id)
    )

    if inventario is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay inventario registrado para este producto en la sede",
        )

    if inventario.stock < payload.cantidad:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock insuficiente para realizar la salida",
        )

    stock_anterior = inventario.stock
    inventario.stock -= payload.cantidad

    movimiento = MovimientoInventario(
        inventario_id=inventario.id,
        usuario_id=usuario_id,
        tipo="SALIDA",
        cantidad=payload.cantidad,
        stock_anterior=stock_anterior,
        stock_nuevo=inventario.stock,
        motivo=payload.motivo,
    )
    db.add(movimiento)
    db.commit()
    db.refresh(inventario)
    return inventario
