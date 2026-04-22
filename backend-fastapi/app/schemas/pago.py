from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PagoCreate(BaseModel):
    pedido_id: int
    metodo_pago: str = Field(min_length=3, max_length=20)
    monto_efectivo: Decimal | None = Field(default=None, ge=0)
    monto_tarjeta: Decimal | None = Field(default=None, ge=0)
    referencia: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def validar_metodo(self) -> "PagoCreate":
        metodo = self.metodo_pago.upper()
        self.metodo_pago = metodo

        if metodo not in {"EFECTIVO", "TARJETA", "MIXTO"}:
            raise ValueError("Metodo de pago invalido")

        if metodo == "EFECTIVO" and self.monto_efectivo is None:
            raise ValueError("Debe enviar monto_efectivo para pagos en efectivo")
        if metodo == "TARJETA" and self.monto_tarjeta is None:
            raise ValueError("Debe enviar monto_tarjeta para pagos con tarjeta")
        if metodo == "MIXTO" and (self.monto_efectivo is None or self.monto_tarjeta is None):
            raise ValueError("Debe enviar monto_efectivo y monto_tarjeta para pagos mixtos")

        return self


class PagoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pedido_id: int
    usuario_id: int
    metodo_pago: str
    monto_total: Decimal
    monto_efectivo: Decimal | None
    monto_tarjeta: Decimal | None
    referencia: str | None
    comprobante: str | None
    creado_en: datetime


class PedidoPendienteCobroResponse(BaseModel):
    id: int
    mesa_id: int
    usuario_id: int
    estado: str
    total: Decimal
