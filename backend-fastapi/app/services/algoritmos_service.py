from __future__ import annotations

from functools import lru_cache
from typing import Any


def _faltante(producto: dict[str, Any]) -> int:
    stock = int(producto.get("stock", 0) or 0)
    umbral = int(producto.get("umbral", producto.get("umbral_minimo", 0)) or 0)
    return max(umbral - stock, 0)


def algoritmo_voraz_reabastecimiento(productos: list[dict[str, Any]], presupuesto: float) -> dict[str, Any]:
    """Prioriza reabastecimiento calculando cantidades por producto.

    Compra primero los productos con mayor faltante y mejor margen, hasta agotar
    el presupuesto o cubrir el faltante recomendado.
    """
    seleccionados: list[dict[str, Any]] = []
    total_usado = 0.0
    presupuesto = max(float(presupuesto), 0)

    productos_ordenados = sorted(
        productos,
        key=lambda p: (
            _faltante(p),
            float(p.get("ganancia", 0) or 0),
            -float(p.get("costo_compra", 0) or 0),
        ),
        reverse=True,
    )

    for producto in productos_ordenados:
        costo = float(producto.get("costo_compra", 0) or 0)
        faltante = _faltante(producto)
        if costo <= 0 or faltante <= 0:
            continue

        presupuesto_restante = presupuesto - total_usado
        cantidad_posible = int(presupuesto_restante // costo)
        cantidad_recomendada = min(faltante, cantidad_posible)
        if cantidad_recomendada <= 0:
            continue

        subtotal = cantidad_recomendada * costo
        item = dict(producto)
        item["faltante"] = faltante
        item["cantidad_recomendada"] = cantidad_recomendada
        item["subtotal"] = subtotal
        item["umbral_minimo"] = int(producto.get("umbral", producto.get("umbral_minimo", 0)) or 0)
        seleccionados.append(item)
        total_usado += subtotal

        if total_usado >= presupuesto:
            break

    return {
        "algoritmo": "Prioridad de reabastecimiento",
        "descripcion": "Sugiere cantidades priorizando productos con mayor necesidad de reposicion.",
        "presupuesto": presupuesto,
        "total_usado": total_usado,
        "saldo": presupuesto - total_usado,
        "productos_seleccionados": seleccionados,
    }


def algoritmo_mochila(productos: list[dict[str, Any]], presupuesto: int) -> dict[str, Any]:
    """Optimiza compra con mochila acotada por unidades faltantes.

    Cada unidad faltante se considera una posible compra. Así el resultado
    recomienda cantidades, no solo productos sueltos.
    """
    presupuesto = max(int(presupuesto), 0)
    unidades: list[dict[str, Any]] = []

    for producto in productos:
        costo = max(int(float(producto.get("costo_compra", 0) or 0)), 0)
        if costo <= 0:
            continue
        faltante = _faltante(producto)
        valor = max(int(float(producto.get("ganancia", producto.get("valor", 1)) or 1)), 1)
        for _ in range(faltante):
            unidades.append({
                "producto_id": producto.get("producto_id"),
                "codigo": producto.get("codigo"),
                "nombre": producto.get("nombre"),
                "stock": producto.get("stock", 0),
                "umbral_minimo": int(producto.get("umbral", producto.get("umbral_minimo", 0)) or 0),
                "faltante": faltante,
                "costo_compra": costo,
                "ganancia": valor,
            })

    n = len(unidades)
    dp = [[0 for _ in range(presupuesto + 1)] for _ in range(n + 1)]

    for i in range(1, n + 1):
        costo = unidades[i - 1]["costo_compra"]
        valor = unidades[i - 1]["ganancia"]
        for capacidad in range(presupuesto + 1):
            dp[i][capacidad] = dp[i - 1][capacidad]
            if costo <= capacidad:
                dp[i][capacidad] = max(dp[i][capacidad], valor + dp[i - 1][capacidad - costo])

    seleccion: dict[Any, dict[str, Any]] = {}
    capacidad = presupuesto
    for i in range(n, 0, -1):
        if dp[i][capacidad] != dp[i - 1][capacidad]:
            unidad = unidades[i - 1]
            key = unidad["producto_id"]
            if key not in seleccion:
                seleccion[key] = {
                    "producto_id": unidad["producto_id"],
                    "codigo": unidad["codigo"],
                    "nombre": unidad["nombre"],
                    "stock": unidad["stock"],
                    "umbral_minimo": unidad["umbral_minimo"],
                    "faltante": unidad["faltante"],
                    "costo_compra": unidad["costo_compra"],
                    "cantidad_recomendada": 0,
                    "subtotal": 0,
                }
            seleccion[key]["cantidad_recomendada"] += 1
            seleccion[key]["subtotal"] += unidad["costo_compra"]
            capacidad -= unidad["costo_compra"]

    seleccionados = list(seleccion.values())
    seleccionados.sort(key=lambda p: (p["faltante"], p["cantidad_recomendada"]), reverse=True)
    total_costo = sum(float(p["subtotal"]) for p in seleccionados)

    return {
        "algoritmo": "Compra recomendada",
        "descripcion": "Optimiza cantidades de compra sin superar el presupuesto disponible.",
        "presupuesto": presupuesto,
        "valor_maximo": dp[n][presupuesto] if n else 0,
        "total_usado": total_costo,
        "saldo": presupuesto - total_costo,
        "productos_seleccionados": seleccionados,
    }


def recursividad_simple_suma(numeros: list[int]) -> int:
    """Recursividad simple: una llamada recursiva por ejecucion."""
    if not numeros:
        return 0
    return numeros[0] + recursividad_simple_suma(numeros[1:])


@lru_cache(maxsize=128)
def recursividad_multiple_fibonacci(n: int) -> int:
    """Recursividad multiple: dos llamadas recursivas."""
    if n <= 0:
        return 0
    if n == 1:
        return 1
    return recursividad_multiple_fibonacci(n - 1) + recursividad_multiple_fibonacci(n - 2)


def recursividad_anidada_aplanar(datos: list[Any]) -> list[Any]:
    """Recursividad anidada: procesa listas dentro de listas."""
    resultado: list[Any] = []
    for item in datos:
        if isinstance(item, list):
            resultado.extend(recursividad_anidada_aplanar(item))
        else:
            resultado.append(item)
    return resultado


def es_par(n: int) -> bool:
    """Recursividad cruzada/indirecta: es_par llama a es_impar."""
    n = abs(n)
    if n == 0:
        return True
    return es_impar(n - 1)


def es_impar(n: int) -> bool:
    """Recursividad cruzada/indirecta: es_impar llama a es_par."""
    n = abs(n)
    if n == 0:
        return False
    return es_par(n - 1)


def recursividad_cruzada_validar(numero: int) -> dict[str, Any]:
    return {
        "numero": numero,
        "es_par": es_par(numero),
        "es_impar": es_impar(numero),
    }
