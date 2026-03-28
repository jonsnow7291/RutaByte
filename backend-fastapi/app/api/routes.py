from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.categoria import Categoria
from app.models.mesa import Mesa
from app.models.producto import Producto
from app.schemas.producto import CategoriaResponse, ProductoResponse

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


@router.get("/mesas", dependencies=[Depends(get_current_user)])
def listar_mesas(db: Session = Depends(get_db)) -> list[dict]:
    stmt = select(Mesa).where(Mesa.activa.is_(True)).order_by(Mesa.identificador_mesa.asc())
    mesas = db.scalars(stmt).all()
    return [
        {"id": m.id, "sede_id": m.sede_id, "identificador_mesa": m.identificador_mesa, "estado": m.estado}
        for m in mesas
    ]
