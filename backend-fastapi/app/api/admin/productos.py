from __future__ import annotations

from datetime import datetime
from decimal import Decimal
import os
import shutil

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_admin
from app.db.session import get_db
from app.models.categoria import Categoria
from app.models.producto import Producto
from app.models.historial_precio import HistorialPrecio
from app.services.algoritmos_service import recursividad_anidada_aplanar
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
    stmt = select(Categoria).order_by(Categoria.activa.desc(), Categoria.nombre.asc())
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


@router.put("/categorias/{categoria_id}", response_model=CategoriaResponse)
def actualizar_categoria(categoria_id: int, payload: CategoriaCreate, db: Session = Depends(get_db)) -> Categoria:
    categoria = db.get(Categoria, categoria_id)
    if categoria is None or not categoria.activa:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria no encontrada")

    existe = db.scalar(
        select(Categoria).where(
            func.lower(Categoria.nombre) == payload.nombre.lower(),
            Categoria.id != categoria_id
        )
    )
    if existe:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe otra categoria con ese nombre")

    categoria.nombre = payload.nombre
    db.commit()
    db.refresh(categoria)
    return categoria


@router.delete("/categorias/{categoria_id}")
def toggle_categoria(categoria_id: int, db: Session = Depends(get_db)) -> dict[str, str | int]:
    categoria = db.get(Categoria, categoria_id)
    if categoria is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria no encontrada")

    categoria.activa = not categoria.activa
    db.commit()
    accion = "activada" if categoria.activa else "desactivada"
    return {"message": f"Categoria {accion} correctamente", "id": categoria_id}




@router.get("/categorias/arbol")
def arbol_categorias_productos(db: Session = Depends(get_db)) -> dict:
    """Recursividad anidada aplicada al catálogo.

    Construye una estructura categoría -> productos y usa recursividad anidada
    para aplanar los nombres. Esto no es un ejercicio aislado: se aplica al
    catálogo real de productos del sistema.
    """
    categorias = list(db.scalars(select(Categoria).where(Categoria.activa.is_(True)).order_by(Categoria.nombre.asc())).all())
    productos = list(db.scalars(select(Producto).where(Producto.activo.is_(True)).order_by(Producto.nombre.asc())).all())

    arbol = []
    estructura_anidada = []
    for categoria in categorias:
        productos_categoria = [
            {
                "id": producto.id,
                "codigo": producto.codigo,
                "nombre": producto.nombre,
                "precio_venta": producto.precio,
                "precio_compra": producto.costo_compra,
            }
            for producto in productos
            if producto.categoria_id == categoria.id
        ]
        arbol.append({"categoria": categoria.nombre, "productos": productos_categoria})
        estructura_anidada.append([categoria.nombre, [p["nombre"] for p in productos_categoria]])

    return {
        "algoritmo_aplicado": "Recursividad anidada",
        "arbol": arbol,
        "nombres_aplanados": recursividad_anidada_aplanar(estructura_anidada),
    }


# ── Productos ───────────────────────────────────────────────

@router.get("", response_model=list[ProductoResponse])
def listar_productos(db: Session = Depends(get_db)) -> list[Producto]:
    stmt = select(Producto).order_by(Producto.activo.desc(), Producto.nombre.asc())
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
def actualizar_producto(
    producto_id: int,
    payload: ProductoUpdate,
    current_user: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> Producto:
    producto = db.get(Producto, producto_id)
    if producto is None or not producto.activo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")

    updates = payload.model_dump(exclude_unset=True)

    if "categoria_id" in updates:
        categoria = db.get(Categoria, updates["categoria_id"])
        if categoria is None or not categoria.activa:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Categoria no valida")

    # Audit and record price history if price changes!
    if "precio" in updates:
        nuevo_precio = Decimal(str(updates["precio"]))
        if nuevo_precio != producto.precio:
            cambiado_por_id = int(current_user.get("usuario_id"))
            historial = HistorialPrecio(
                producto_id=producto.id,
                precio_anterior=producto.precio,
                precio_nuevo=nuevo_precio,
                cambiado_por=cambiado_por_id,
            )
            db.add(historial)

    for field, value in updates.items():
        setattr(producto, field, value)

    db.commit()
    db.refresh(producto)
    return producto


@router.delete("/{producto_id}")
def toggle_producto(producto_id: int, db: Session = Depends(get_db)) -> dict[str, str | int]:
    producto = db.get(Producto, producto_id)
    if producto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")

    producto.activo = not producto.activo
    db.commit()
    db.refresh(producto)
    accion = "activado" if producto.activo else "desactivado"
    return {"message": f"Producto {accion} correctamente", "id": producto.id}


@router.post("/{producto_id}/imagen", response_model=ProductoResponse)
def subir_imagen_producto(
    producto_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> Producto:
    producto = db.get(Producto, producto_id)
    if producto is None or not producto.activo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")

    # Validate extension
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["jpg", "jpeg", "png", "webp", "gif"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de imagen no permitido")

    # Save to local folder static/uploads
    filename = f"prod_{producto_id}_{int(datetime.now().timestamp())}.{ext}"
    file_path = os.path.join("static/uploads", filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Save relative URL
    producto.url_imagen = f"/static/uploads/{filename}"
    db.commit()
    db.refresh(producto)
    return producto
