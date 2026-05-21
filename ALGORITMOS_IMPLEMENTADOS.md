# Algoritmos implementados dentro del flujo RutaByte

Los algoritmos no quedaron como una pantalla aislada. Quedaron integrados en módulos reales del sistema.

## 1. Algoritmo voraz

**Ubicación:** Inventario de la sede.

**Endpoint:** `GET /cajero/inventario/sugerencia-voraz?sede_id=&presupuesto=`

**Uso:** prioriza productos con mayor urgencia de reabastecimiento según:

- stock actual,
- umbral mínimo,
- costo de compra,
- ganancia estimada.

En el frontend se ve dentro de `inventario.html`, sección **Algoritmos aplicados al inventario**.

---

## 2. Algoritmo de la mochila 0/1

**Ubicación:** Inventario de la sede.

**Endpoint:** `GET /cajero/inventario/optimizar-compra?sede_id=&presupuesto=`

**Uso:** selecciona la combinación de productos más conveniente para comprar sin superar el presupuesto disponible.

En el frontend se ve dentro de `inventario.html`, sección **Algoritmos aplicados al inventario**.

---

## 3. Recursividad simple

**Ubicación:** Reportes de ventas.

**Endpoint:** `GET /reportes/ventas/resumen-recursivo`

**Uso:** suma de manera recursiva los totales de venta, costo y ganancia de las ventas consultadas.

---

## 4. Recursividad múltiple

**Ubicación:** Reportes de ventas.

**Endpoint:** `GET /reportes/ventas/resumen-recursivo`

**Uso:** cálculo de un escenario académico de crecimiento mediante Fibonacci, usando múltiples llamadas recursivas.

---

## 5. Recursividad anidada

**Ubicación:** Catálogo de productos y categorías.

**Endpoint:** `GET /admin/productos/categorias/arbol`

**Uso:** recorre categorías con listas de productos y aplana una estructura anidada para análisis del catálogo.

---

## 6. Recursividad cruzada o indirecta

**Ubicación:** Parametrización de mesas.

**Archivo:** `backend-fastapi/app/api/mesas.py`

**Uso:** se ejecuta una validación académica con funciones cruzadas `es_par()` y `es_impar()` dentro del flujo real de creación/edición de mesas.

---

## Archivos principales

- `backend-fastapi/app/services/algoritmos_service.py`
- `backend-fastapi/app/api/cajero/inventario.py`
- `backend-fastapi/app/api/reportes.py`
- `backend-fastapi/app/api/admin/productos.py`
- `backend-fastapi/app/api/mesas.py`
- `frontend-vanilla/inventario.html`
- `frontend-vanilla/js/inventario.js`
