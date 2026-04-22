from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# 🔥 IMPORTANTE: importar TODOS los modelos
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.sede import Sede
from app.models.categoria import Categoria
from app.models.producto import Producto
from app.models.mesa import Mesa
from app.models.pedido import Pedido
from app.models.detalle_pedido import DetallePedido
from app.models.inventario import Inventario
from app.models.movimiento_inventario import MovimientoInventario
from app.models.pago import Pago