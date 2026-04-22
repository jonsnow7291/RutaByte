from sqlalchemy.orm import Session
from app.models.mesa import Mesa
from app.schemas.mesa import MesaCreate, MesaUpdate

# 🔹 Crear
def crear_mesa(db: Session, mesa: MesaCreate):
    nueva = Mesa(**mesa.dict())
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva


# 🔹 Obtener todas
def obtener_mesas(db: Session):
    return db.query(Mesa).all()


# 🔹 Obtener por sede
def obtener_mesas_por_sede(db: Session, sede_id: int):
    return db.query(Mesa).filter(Mesa.sede_id == sede_id).all()


# 🔹 🔥 ACTUALIZAR (IMPORTANTE)
def actualizar_mesa(db: Session, mesa_id: int, datos: MesaUpdate):
    mesa = db.query(Mesa).filter(Mesa.id == mesa_id).first()

    if not mesa:
        return None

    # actualizar campos SOLO si vienen
    if datos.sede_id is not None:
        mesa.sede_id = datos.sede_id

    if datos.identificador_mesa is not None:
        mesa.identificador_mesa = datos.identificador_mesa

    if datos.estado is not None:
        mesa.estado = datos.estado

    if datos.activa is not None:
        mesa.activa = datos.activa

    db.commit()          # 🔥 CLAVE
    db.refresh(mesa)     # 🔥 CLAVE

    return mesa


# 🔹 Eliminar (soft delete)
def eliminar_mesa(db: Session, mesa_id: int):
    mesa = db.query(Mesa).filter(Mesa.id == mesa_id).first()

    if not mesa:
        return None

    mesa.activa = False

    db.commit()          # 🔥 CLAVE
    db.refresh(mesa)

    return mesa