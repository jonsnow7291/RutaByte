from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.dependencies.auth import get_current_mesero
from app.db.session import get_db
from app.models.detalle_pedido import DetallePedido
from app.models.mesa import Mesa
from app.models.pedido import Pedido
from app.models.producto import Producto
from app.schemas.pedido import PedidoCreate, PedidoListResponse, PedidoResponse
from app.services.inventario_service import descontar_inventario


router = APIRouter(
    prefix="/mesero/pedidos",
    tags=["mesero-pedidos"],
)


@router.post("", response_model=PedidoResponse, status_code=status.HTTP_201_CREATED)
def crear_pedido(
    payload: PedidoCreate,
    current_user: dict = Depends(get_current_mesero),
    db: Session = Depends(get_db),
) -> Pedido:
    mesa = db.get(Mesa, payload.mesa_id)
    if mesa is None or not mesa.activa:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mesa no valida")

    usuario_id = int(current_user.get("usuario_id"))

    pedido = Pedido(
        mesa_id=payload.mesa_id,
        usuario_id=usuario_id,
        estado="EN_PREPARACION",
    )

    try:
        for item in payload.items:
            producto = db.get(Producto, item.producto_id)
            if producto is None or not producto.activo:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Producto con id {item.producto_id} no valido",
                )

            descontar_inventario(
                db=db,
                sede_id=mesa.sede_id,
                producto_id=item.producto_id,
                cantidad=item.cantidad,
                usuario_id=usuario_id,
            )

            pedido.detalles.append(
                DetallePedido(
                    producto_id=item.producto_id,
                    cantidad=item.cantidad,
                    precio_unitario=producto.precio,
                    costo_unitario=producto.costo_compra,
                    notas=item.notas,
                )
            )

        mesa.estado = "OCUPADA"
        db.add(pedido)
        db.commit()
        db.refresh(pedido)
        return pedido
    except HTTPException:
        db.rollback()
        raise
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al crear el pedido") from exc


@router.get("", response_model=list[PedidoListResponse])
def listar_pedidos(
    current_user: dict = Depends(get_current_mesero),
    db: Session = Depends(get_db),
) -> list[Pedido]:
    usuario_id = int(current_user.get("usuario_id"))
    stmt = (
        select(Pedido)
        .where(Pedido.usuario_id == usuario_id)
        .order_by(Pedido.creado_en.desc())
    )
    return list(db.scalars(stmt).all())


@router.get("/{pedido_id}", response_model=PedidoResponse)
def obtener_pedido(
    pedido_id: int,
    current_user: dict = Depends(get_current_mesero),
    db: Session = Depends(get_db),
) -> Pedido:
    role_id = int(current_user.get("rol_id", current_user.get("role_id")))
    usuario_id = int(current_user.get("usuario_id"))

    stmt = select(Pedido).options(selectinload(Pedido.detalles)).where(Pedido.id == pedido_id)
    if role_id != 1:
        stmt = stmt.where(Pedido.usuario_id == usuario_id)

    pedido = db.scalar(stmt)
    if pedido is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
    return pedido


@router.patch("/{pedido_id}/estado")
def cambiar_estado(
    pedido_id: int,
    current_user: dict = Depends(get_current_mesero),
    db: Session = Depends(get_db),
) -> dict[str, str | int]:
    role_id = int(current_user.get("rol_id", current_user.get("role_id")))
    usuario_id = int(current_user.get("usuario_id"))

    pedido = db.get(Pedido, pedido_id)
    if pedido is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
    if role_id != 1 and pedido.usuario_id != usuario_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puede modificar este pedido")

    transiciones = {
        "EN_PREPARACION": "LISTO",
        "LISTO": "ENTREGADO",
    }

    siguiente = transiciones.get(pedido.estado)
    if siguiente is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede avanzar el estado desde {pedido.estado}",
        )

    pedido.estado = siguiente
    db.commit()
    return {"message": f"Pedido actualizado a {siguiente}", "id": pedido.id, "estado": siguiente}
