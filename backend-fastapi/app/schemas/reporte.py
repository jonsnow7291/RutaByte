from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class ReporteVentaItem(BaseModel):
    fecha: datetime
    sede_id: int
    sede: str
    codigo_producto: str
    producto: str
    unidades_vendidas: int
    precio_compra: Decimal
    precio_venta: Decimal
    venta_total: Decimal
    costo_total: Decimal
    ganancia: Decimal
