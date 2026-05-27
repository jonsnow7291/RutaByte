from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.categoria import Categoria
from app.models.mesa import Mesa
from app.models.producto import Producto
from app.models.sede import Sede
from app.schemas.producto import CategoriaResponse, ProductoResponse
from app.schemas.sede import SedeResponse

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/productos", response_model=list[ProductoResponse], dependencies=[Depends(get_current_user)])
def listar_productos_publico(db: Session = Depends(get_db)) -> list[Producto]:
    stmt = select(Producto).where(Producto.activo.is_(True)).order_by(Producto.nombre.asc())
    return list(db.scalars(stmt).all())


@router.get("/categorias", response_model=list[CategoriaResponse], dependencies=[Depends(get_current_user)])
def listar_categorias_publico(db: Session = Depends(get_db)) -> list[Categoria]:
    stmt = select(Categoria).where(Categoria.activa.is_(True)).order_by(Categoria.nombre.asc())
    return list(db.scalars(stmt).all())


@router.get("/sedes", response_model=list[SedeResponse], dependencies=[Depends(get_current_user)])
def listar_sedes_publico(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Sede]:
    role_id = int(current_user.get("rol_id", current_user.get("role_id", 0)))
    stmt = select(Sede).where(Sede.activa.is_(True))

    # Admin ve todas las sedes. Cajero y mesero solo ven la sede asignada.
    if role_id != 1:
        user_sede_id = current_user.get("sede_id")
        if user_sede_id is None:
            return []
        stmt = stmt.where(Sede.id == int(user_sede_id))

    stmt = stmt.order_by(Sede.nombre.asc())
    return list(db.scalars(stmt).all())


@router.get("/mesas")
def listar_mesas(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    role_id = int(current_user.get("rol_id", current_user.get("role_id", 0)))
    stmt = select(Mesa)

    # Admin ve todas las mesas. Mesero y cajero solo ven las mesas de su sede.
    if role_id != 1:
        user_sede_id = current_user.get("sede_id")
        if user_sede_id is None:
            return []
        stmt = stmt.where(Mesa.sede_id == int(user_sede_id))

    stmt = stmt.order_by(Mesa.activa.desc(), Mesa.sede_id.asc(), Mesa.identificador_mesa.asc())
    mesas = db.scalars(stmt).all()
    return [
        {"id": m.id, "sede_id": m.sede_id, "identificador_mesa": m.identificador_mesa, "estado": m.estado, "activa": m.activa}
        for m in mesas
    ]
