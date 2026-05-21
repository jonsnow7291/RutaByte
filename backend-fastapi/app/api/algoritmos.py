from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.dependencies.auth import get_current_admin
from app.services.algoritmos_service import (
    algoritmo_mochila,
    algoritmo_voraz_reabastecimiento,
    recursividad_anidada_aplanar,
    recursividad_cruzada_validar,
    recursividad_multiple_fibonacci,
    recursividad_simple_suma,
)

router = APIRouter(
    prefix="/admin/algoritmos",
    tags=["admin-algoritmos"],
    dependencies=[Depends(get_current_admin)],
)


class ProductoAlgoritmo(BaseModel):
    nombre: str = Field(min_length=1, max_length=150)
    stock: int = Field(ge=0)
    umbral: int = Field(ge=0)
    costo_compra: int = Field(gt=0)
    ganancia: int = Field(default=0, ge=0)
    valor: int = Field(default=0, ge=0)


class AlgoritmosRequest(BaseModel):
    presupuesto: int = Field(gt=0)
    productos: list[ProductoAlgoritmo] = Field(min_length=1)


class RecursividadRequest(BaseModel):
    numeros: list[int] = Field(default_factory=lambda: [1, 2, 3, 4, 5])
    numero: int = Field(default=6, ge=0, le=30)
    datos_anidados: list[Any] = Field(default_factory=lambda: [1, [2, 3], [4, [5, 6]]])


@router.post("/voraz")
def ejecutar_voraz(payload: AlgoritmosRequest) -> dict[str, Any]:
    productos = [producto.model_dump() for producto in payload.productos]
    return algoritmo_voraz_reabastecimiento(productos, payload.presupuesto)


@router.post("/mochila")
def ejecutar_mochila(payload: AlgoritmosRequest) -> dict[str, Any]:
    productos = [producto.model_dump() for producto in payload.productos]
    return algoritmo_mochila(productos, payload.presupuesto)


@router.post("/recursividad")
def ejecutar_recursividad(payload: RecursividadRequest) -> dict[str, Any]:
    return {
        "recursividad_simple": {
            "descripcion": "Suma recursiva de una lista de numeros.",
            "entrada": payload.numeros,
            "resultado": recursividad_simple_suma(payload.numeros),
        },
        "recursividad_multiple": {
            "descripcion": "Fibonacci con dos llamadas recursivas.",
            "entrada": payload.numero,
            "resultado": recursividad_multiple_fibonacci(payload.numero),
        },
        "recursividad_anidada": {
            "descripcion": "Aplanamiento de estructura anidada.",
            "entrada": payload.datos_anidados,
            "resultado": recursividad_anidada_aplanar(payload.datos_anidados),
        },
        "recursividad_cruzada_indirecta": {
            "descripcion": "Funciones es_par y es_impar llamandose entre si.",
            "entrada": payload.numero,
            "resultado": recursividad_cruzada_validar(payload.numero),
        },
    }
