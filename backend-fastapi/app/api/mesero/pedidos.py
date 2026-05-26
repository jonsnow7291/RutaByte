import asyncio
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.dependencies.auth import get_current_mesero
from app.db.session import get_db
from app.models.detalle_pedido import DetallePedido
from app.models.mesa import Mesa
from app.models.pedido import Pedido
from app.models.producto import Producto
from app.schemas.pedido import PedidoCreate, PedidoListResponse, PedidoResponse, DetalleItemCancelar
from app.core.notifications import notification_manager


router = APIRouter(
    prefix="/mesero/pedidos",
    tags=["mesero-pedidos"],
)


def _validar_mesa_de_sede(mesa: Mesa, current_user: dict) -> None:
    """Evita que meseros/cajeros operen mesas de otra sede.

    El administrador puede operar cualquier sede; los demás roles quedan
    restringidos a la sede_id incluida en su JWT.
    """
    role_id = int(current_user.get("rol_id", current_user.get("role_id", 0)))
    if role_id == 1:
        return

    user_sede_id = current_user.get("sede_id")
    if user_sede_id is None or int(user_sede_id) != int(mesa.sede_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puede operar mesas o pedidos de otra sede",
        )


def _safe_broadcast(message: dict) -> None:
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(notification_manager.broadcast(message))
    except RuntimeError:
        pass


def _validar_pedido_de_sede(pedido: Pedido, current_user: dict, db: Session) -> None:
    mesa = db.get(Mesa, pedido.mesa_id)
    if mesa is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mesa no encontrada")
    _validar_mesa_de_sede(mesa, current_user)


@router.post("", response_model=PedidoResponse, status_code=status.HTTP_201_CREATED)
def crear_pedido(
    payload: PedidoCreate,
    current_user: dict = Depends(get_current_mesero),
    db: Session = Depends(get_db),
) -> Pedido:
    mesa = db.get(Mesa, payload.mesa_id)
    if mesa is None or not mesa.activa:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mesa no valida")
    _validar_mesa_de_sede(mesa, current_user)

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

            # NOTE: We have removed the comanda-time inventory discount (descontar_inventario)
            # from here, and moved it to payment time to achieve atomic transaction sync.

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

        # Broadcast WebSocket notification!
        _safe_broadcast(
            {
                "evento": "NUEVO_PEDIDO",
                "pedido_id": pedido.id,
                "mesa_id": pedido.mesa_id,
                "identificador_mesa": mesa.identificador_mesa,
                "sede_id": mesa.sede_id,
                "mensaje": f"Nuevo pedido #{pedido.id} creado para la Mesa {mesa.identificador_mesa}",
            }
        )

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
    role_id = int(current_user.get("rol_id", current_user.get("role_id", 0)))
    usuario_id = int(current_user.get("usuario_id"))
    stmt = select(Pedido).join(Mesa, Pedido.mesa_id == Mesa.id).order_by(Pedido.creado_en.desc())

    if role_id == 1:
        return list(db.scalars(stmt).all())

    user_sede_id = current_user.get("sede_id")
    if user_sede_id is None:
        return []

    stmt = stmt.where(
        Pedido.usuario_id == usuario_id,
        Mesa.sede_id == int(user_sede_id),
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
    _validar_pedido_de_sede(pedido, current_user, db)
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
    _validar_pedido_de_sede(pedido, current_user, db)
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

    # Broadcast WebSocket notification!
    _safe_broadcast(
        {
            "evento": "CAMBIO_ESTADO_PEDIDO",
            "pedido_id": pedido.id,
            "estado": siguiente,
            "mensaje": f"El pedido #{pedido.id} cambió a estado {siguiente}",
        }
    )

    return {"message": f"Pedido actualizado a {siguiente}", "id": pedido.id, "estado": siguiente}


@router.post("/{pedido_id}/detalles/{detalle_id}/cancelar")
def cancelar_item(
    pedido_id: int,
    detalle_id: int,
    payload: DetalleItemCancelar,
    current_user: dict = Depends(get_current_mesero),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    pedido = db.get(Pedido, pedido_id)
    if pedido is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
    _validar_pedido_de_sede(pedido, current_user, db)

    if pedido.estado in ("PAGADO", "CANCELADO"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pueden cancelar ítems de un pedido pagado o cancelado",
        )

    detalle = db.get(DetallePedido, detalle_id)
    if detalle is None or detalle.pedido_id != pedido_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Detalle de pedido no encontrado")

    if detalle.cancelado:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El ítem ya se encuentra cancelado")

    usuario_id = int(current_user.get("usuario_id"))
    detalle.cancelado = True
    detalle.justificacion_cancelacion = payload.justificacion
    detalle.cancelado_por = usuario_id

    db.commit()

    # Broadcast item cancellation to kitchen WebSocket
    _safe_broadcast(
        {
            "evento": "ANULACION_ITEM",
            "pedido_id": pedido.id,
            "detalle_id": detalle.id,
            "producto_id": detalle.producto_id,
            "justificacion": payload.justificacion,
            "mensaje": f"Ítem anulado en pedido #{pedido.id}: {payload.justificacion}",
        }
    )

    return {"message": "Item cancelado correctamente"}


@router.post("/{pedido_id}/transferir")
def transferir_pedido(
    pedido_id: int,
    mesa_destino_id: int = Query(..., alias="mesa_destino_id"),
    current_user: dict = Depends(get_current_mesero),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    pedido = db.get(Pedido, pedido_id)
    if pedido is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
    _validar_pedido_de_sede(pedido, current_user, db)

    if pedido.estado in ("PAGADO", "CANCELADO"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede transferir un pedido pagado o cancelado",
        )

    mesa_origen = db.get(Mesa, pedido.mesa_id)
    mesa_destino = db.get(Mesa, mesa_destino_id)

    if mesa_destino is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mesa destino no encontrada")

    _validar_mesa_de_sede(mesa_destino, current_user)

    if not mesa_destino.activa or mesa_destino.estado != "LIBRE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La mesa destino no está disponible o no se encuentra libre",
        )

    old_mesa_id = pedido.mesa_id
    old_identificador = mesa_origen.identificador_mesa if mesa_origen else f"ID {old_mesa_id}"
    new_identificador = mesa_destino.identificador_mesa

    # Swap table
    pedido.mesa_id = mesa_destino_id
    if mesa_origen:
        mesa_origen.estado = "LIBRE"
    mesa_destino.estado = "OCUPADA"

    db.commit()

    # Broadcast layout change to WebSocket
    _safe_broadcast(
        {
            "evento": "TRANSFERENCIA_PEDIDO",
            "pedido_id": pedido.id,
            "mesa_origen_id": old_mesa_id,
            "mesa_destino_id": mesa_destino_id,
            "mensaje": f"Pedido #{pedido.id} transferido de Mesa {old_identificador} a Mesa {new_identificador}",
        }
    )

    return {"message": f"Pedido transferido con éxito de Mesa {old_identificador} a Mesa {new_identificador}"}
