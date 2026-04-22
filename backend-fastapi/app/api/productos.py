from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.producto import Producto
from app.schemas.producto import ProductoCreate, ProductoUpdate

router = APIRouter(prefix="/api/productos", tags=["Productos"])

# 🔹 LISTAR
@router.get("/")
def listar(db: Session = Depends(get_db)):
    return db.query(Producto).all()

# 🔹 CREAR
@router.post("/")
def crear(data: ProductoCreate, db: Session = Depends(get_db)):
    nuevo = Producto(**data.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

# 🔹 OBTENER UNO
@router.get("/{id}")
def obtener(id: int, db: Session = Depends(get_db)):
    return db.query(Producto).get(id)

# 🔹 ACTUALIZAR
@router.put("/{id}")
def actualizar(id: int, data: ProductoUpdate, db: Session = Depends(get_db)):
    producto = db.query(Producto).get(id)
    for key, value in data.dict(exclude_unset=True).items():
        setattr(producto, key, value)
    db.commit()
    return producto

# 🔹 ELIMINAR
@router.delete("/{id}")
def eliminar(id: int, db: Session = Depends(get_db)):
    producto = db.query(Producto).get(id)
    db.delete(producto)
    db.commit()
    return {"message": "Producto eliminado"}