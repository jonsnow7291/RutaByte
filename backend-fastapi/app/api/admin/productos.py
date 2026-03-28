from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_admin
from app.db.session import get_db
from app.models.categoria import Categoria
from app.models.producto import Producto
from app.schemas.producto import (
    CategoriaCreate,
    CategoriaResponse,
    ProductoCreate,
    ProductoResponse,
    ProductoUpdate,
)


router = APIRouter(
    prefix="/admin/productos",
    tags=["admin-productos"],
    dependencies=[Depends(get_current_admin)],
)


# ── Categorías ──────────────────────────────────────────────

@router.get("/categorias", response_model=list[CategoriaResponse])
def listar_categorias(db: Session = Depends(get_db)) -> list[Categoria]:
    stmt = select(Categoria).where(Categoria.activa.is_(True)).order_by(Categoria.nombre.asc())
    return list(db.scalars(stmt).all())


@router.post("/categorias", response_model=CategoriaResponse, status_code=status.HTTP_201_CREATED)
def crear_categoria(payload: CategoriaCreate, db: Session = Depends(get_db)) -> Categoria:
    existe = db.scalar(
        select(Categoria).where(func.lower(Categoria.nombre) == payload.nombre.lower())
    )
    if existe:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe una categoria con ese nombre")

    categoria = Categoria(nombre=payload.nombre, activa=True)
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria


# ── Productos ───────────────────────────────────────────────

@router.get("", response_model=list[ProductoResponse])
def listar_productos(db: Session = Depends(get_db)) -> list[Producto]:
    stmt = select(Producto).where(Producto.activo.is_(True)).order_by(Producto.nombre.asc())
    return list(db.scalars(stmt).all())


@router.post("", response_model=ProductoResponse, status_code=status.HTTP_201_CREATED)
def crear_producto(payload: ProductoCreate, db: Session = Depends(get_db)) -> Producto:
    categoria = db.get(Categoria, payload.categoria_id)
    if categoria is None or not categoria.activa:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Categoria no valida")

    producto = Producto(**payload.model_dump())
    db.add(producto)
    db.commit()
    db.refresh(producto)
    return producto


@router.put("/{producto_id}", response_model=ProductoResponse)
def actualizar_producto(producto_id: int, payload: ProductoUpdate, db: Session = Depends(get_db)) -> Producto:
    producto = db.get(Producto, producto_id)
    if producto is None or not producto.activo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")

    updates = payload.model_dump(exclude_unset=True)

    if "categoria_id" in updates:
        categoria = db.get(Categoria, updates["categoria_id"])
        if categoria is None or not categoria.activa:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Categoria no valida")

    for field, value in updates.items():
        setattr(producto, field, value)

    db.commit()
    db.refresh(producto)
    return producto


@router.delete("/{producto_id}")
def desactivar_producto(producto_id: int, db: Session = Depends(get_db)) -> dict[str, str | int]:
    producto = db.get(Producto, producto_id)
    if producto is None or not producto.activo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")

    producto.activo = False
    db.commit()
    db.refresh(producto)
    return {"message": "Producto desactivado correctamente", "id": producto.id}
