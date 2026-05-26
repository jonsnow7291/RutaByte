# 🧠 Algoritmos Académicos e Integración Práctica

Uno de los principales valores diferenciadores de **RutaByte** es que sus requisitos académicos no se diseñaron como pantallas aisladas o laboratorios teóricos, sino que se integraron directamente en la lógica operativa real de los flujos de negocio.

A continuación, se detalla el funcionamiento científico, la implementación de código, las complejidades computacionales (Big O) y la visualización en la UI de cada uno de los 6 algoritmos del sistema.

---

## 🟩 1. Algoritmo Voraz (Greedy)

**Objetivo:** Sugerir las cantidades de productos a reabastecer en el almacén de una sede, priorizando de forma óptima bajo un presupuesto dado.

### Ubicación del Código
- **Backend (Lógica):** [algoritmos_service.py](../backend-fastapi/app/services/algoritmos_service.py) -> `algoritmo_voraz_reabastecimiento`
- **Backend (Endpoint):** [inventario.py](../backend-fastapi/app/api/cajero/inventario.py) -> `GET /cajero/inventario/sugerencia-voraz`
- **Frontend (UI):** [inventario.js](../frontend-vanilla/js/inventario.js) y [inventario.html](../frontend-vanilla/inventario.html)

### Funcionamiento y Reglas de Decisión
El algoritmo calcula el **faltante** de cada producto respecto a su stock y umbral mínimo.
$$\text{Faltante} = \max(\text{umbral\_minimo} - \text{stock}, 0)$$

Para tomar decisiones locales óptimas en cada paso, ordena el catálogo de productos con una clave de ordenamiento compuesta:
1. **Faltante (Descendente):** Da prioridad absoluta a los productos que están más urgentes o críticamente vacíos.
2. **Ganancia Unitario (Descendente):** A igualdad de urgencia, prioriza productos con mayor margen de utilidad comercial.
3. **Costo de Compra (Ascendente):** A igualdad de urgencia y ganancia, prefiere los productos más económicos de adquirir para maximizar el rendimiento del capital restante.

Posteriormente, recorre los productos ordenados e intenta comprar unidades hasta cubrir el faltante o agotar el presupuesto.

### Complejidad Computacional
- **Temporal:** $\mathcal{O}(N \log N)$ donde $N$ es el número de productos en inventario, debido a la ordenación del arreglo.
- **Espacial:** $\mathcal{O}(N)$ para almacenar la lista ordenada y los elementos recomendados.

### Código Fuente Explicado
```python
def algoritmo_voraz_reabastecimiento(productos: list[dict[str, Any]], presupuesto: float) -> dict[str, Any]:
    seleccionados: list[dict[str, Any]] = []
    total_usado = 0.0
    presupuesto = max(float(presupuesto), 0)

    # Ordenamiento greedy multivariable
    productos_ordenados = sorted(
        productos,
        key=lambda p: (
            _faltante(p),                      # 1. Mayor necesidad de reposición
            float(p.get("ganancia", 0) or 0),   # 2. Mayor ganancia estimada
            -float(p.get("costo_compra", 0) or 0), # 3. Menor costo de compra
        ),
        reverse=True
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
        seleccionados.append(item)
        total_usado += subtotal

        if total_usado >= presupuesto:
            break

    return {
        "algoritmo": "Prioridad de reabastecimiento (Voraz)",
        "presupuesto": presupuesto,
        "total_usado": total_usado,
        "saldo": presupuesto - total_usado,
        "productos_seleccionados": seleccionados
    }
```

---

## 🎒 2. Algoritmo de la Mochila 0/1 (Programación Dinámica)

**Objetivo:** Maximizar el valor total (ganancia comercial) de los productos a comprar para abastecer una sede, respetando un presupuesto límite, asumiendo que cada producto a adquirir es un objeto discreto e indivisible.

### Ubicación del Código
- **Backend (Lógica):** [algoritmos_service.py](../backend-fastapi/app/services/algoritmos_service.py) -> `algoritmo_mochila`
- **Backend (Endpoint):** [inventario.py](../backend-fastapi/app/api/cajero/inventario.py) -> `GET /cajero/inventario/optimizar-compra`
- **Frontend (UI):** [inventario.js](../frontend-vanilla/js/inventario.js)

### Innovación Académica (Mochila Bounded/Acotada)
En la teoría tradicional de la mochila 0/1, solo se puede elegir "un elemento" (comprar o no comprar el producto). Para solucionar esto en un inventario real con múltiples existencias requeridas, el algoritmo expande el problema:
- Si un producto necesita $K$ unidades para alcanzar su umbral de stock, el algoritmo inserta $K$ **instancias independientes** de ese producto en la lista de unidades posibles.
- Cada instancia tiene su peso (costo de compra) y su beneficio (ganancia estimada del producto).
- Esto nos permite aplicar el algoritmo clásico de la mochila 0/1 y obtener como resultado la **cantidad óptima de unidades a comprar por producto**, en lugar de elegir únicamente productos binarios.

### Ecuación de Recurrencia (Programación Dinámica)
Siendo $dp[i][c]$ el valor máximo acumulado considerando los primeros $i$ elementos y una capacidad presupuestaria de $c$:

$$dp[i][c] = \max(dp[i-1][c], \text{valor}_i + dp[i-1][c - \text{costo}_i])$$

### Complejidad Computacional
- **Temporal:** $\mathcal{O}(U \cdot P)$ donde $U$ es la sumatoria de las unidades faltantes críticas y $P$ es el presupuesto límite (representa el tamaño de la matriz de DP).
- **Espacial:** $\mathcal{O}(U \cdot P)$ para almacenar la matriz de memorización del estado de la mochila.

---

## ➕ 3. Recursividad Simple

**Objetivo:** Calcular la consolidación contable total (ventas, costos y ganancias) de un lote de transacciones filtradas para reportes.

### Ubicación del Código
- **Backend (Lógica):** [algoritmos_service.py](../backend-fastapi/app/services/algoritmos_service.py) -> `recursividad_simple_suma`
- **Backend (Endpoint):** [reportes.py](../backend-fastapi/app/api/reportes.py) -> `GET /reportes/ventas/resumen-recursivo`
- **Frontend (UI):** [reportes.js](../frontend-vanilla/js/reportes.js) y [reportes.html](../frontend-vanilla/reportes.html)

### Explicación
En lugar de iterar con un bucle imperativo (`for` o `while`), el sistema procesa los valores contables en memoria sumando recursivamente la cabeza de la lista con el resultado de procesar la cola de la lista (enfoque funcional de pila).

### Código Fuente
```python
def recursividad_simple_suma(numeros: list[int]) -> int:
    if not numeros:
        return 0
    return numeros[0] + recursividad_simple_suma(numeros[1:])
```
- **Caso Base:** Si la lista está vacía, retorna 0.
- **Caso Recursivo:** Suma el elemento actual con la evaluación recursiva del segmento posterior de la lista.
- **Complejidad:** Temporal $\mathcal{O}(N)$ y Espacial $\mathcal{O}(N)$ (por los frames creados en la pila de llamadas de la memoria RAM).

---

## 📈 4. Recursividad Múltiple

**Objetivo:** Calcular un escenario matemático predictivo de crecimiento de órdenes de venta basado en la secuencia de Fibonacci.

### Ubicación del Código
- **Backend (Lógica):** [algoritmos_service.py](../backend-fastapi/app/services/algoritmos_service.py) -> `recursividad_multiple_fibonacci`
- **Backend (Endpoint):** [reportes.py](../backend-fastapi/app/api/reportes.py) -> `GET /reportes/ventas/resumen-recursivo`

### Explicación y Optimización (`lru_cache`)
La secuencia recursiva múltiple clásica de Fibonacci es ineficiente debido a la re-evaluación redundante de ramas del árbol de llamadas:

```text
                     F(4)
                   /      \
                F(3)      F(2)
               /    \     /    \
             F(2)   F(1) F(1)  F(0)
```

Para prevenir fallos por desbordamiento de pila y retrasos de rendimiento en el servidor, la función en el backend implementa **Memorización** usando el decorador `@lru_cache` de Python, reduciendo drásticamente su costo.
Además, el endpoint limita la entrada del cálculo a un rango máximo razonable para proteger el hardware ($\le 20$ en producción real).

### Complejidad Computacional
- **Clásica:** Temporal $\mathcal{O}(2^n)$ / Espacial $\mathcal{O}(n)$
- **Con Memoization (`lru_cache`):** Temporal $\mathcal{O}(n)$ / Espacial $\mathcal{O}(n)$

---

## 🌳 5. Recursividad Anidada

**Objetivo:** Recorrer y estructurar jerárquicamente un árbol del catálogo (Categoría $\to$ Subcategorías/Productos) y aplanar recursivamente todas las ramas de textos de nombres en una lista plana bidimensional para análisis de consistencia.

### Ubicación del Código
- **Backend (Lógica):** [algoritmos_service.py](../backend-fastapi/app/services/algoritmos_service.py) -> `recursividad_anidada_aplanar`
- **Backend (Endpoint):** [productos.py](../backend-fastapi/app/api/admin/productos.py) -> `GET /admin/productos/categorias/arbol`
- **Frontend (UI):** [productos.js](../frontend-vanilla/js/productos.js) y [productos.html](../frontend-vanilla/productos.html)

### Explicación
Es un algoritmo diseñado para procesar estructuras anidadas cuya profundidad se desconoce en tiempo de diseño. Si encuentra una lista como elemento en el recorrido de la lista padre, se llama a sí mismo pasándole dicha sublista, concatenando los elementos encontrados al regresar en la pila.

### Código Fuente
```python
def recursividad_anidada_aplanar(datos: list[Any]) -> list[Any]:
    resultado: list[Any] = []
    for item in datos:
        if isinstance(item, list):
            # Caso Recursivo Anidado: Aplane la sublista interna
            resultado.extend(recursividad_anidada_aplanar(item))
        else:
            # Caso Base: Almacene el dato atómico
            resultado.append(item)
    return resultado
```
- **Complejidad:** Temporal $\mathcal{O}(M)$ donde $M$ es el número total de nodos hojas y ramificaciones de la estructura anidada.

---

## 🔀 6. Recursividad Cruzada o Indirecta

**Objetivo:** Ejecutar una validación académica mutua del identificador de las mesas del restaurante durante su flujo de creación y edición.

### Ubicación del Código
- **Backend (Lógica):** [algoritmos_service.py](../backend-fastapi/app/services/algoritmos_service.py) -> `es_par` / `es_impar` / `recursividad_cruzada_validar`
- **Backend (Endpoint):** [mesas.py](../backend-fastapi/app/api/mesas.py) -> `POST /api/mesas` y `PUT /api/mesas/{id}`
- **Frontend (UI):** [mesas.js](../frontend-vanilla/js/mesas.js) y [mesas.html](../frontend-vanilla/mesas.html)

### Explicación
La recursividad cruzada se caracteriza porque la función $A$ no se llama a sí misma de manera directa, sino que llama a la función $B$, y la función $B$ llama nuevamente a la función $A$.
En **RutaByte**, esta validación examina la longitud de caracteres del código asignado a la mesa (`identificador_mesa`) para clasificar si posee longitud par o impar, validando el cumplimiento estricto del estándar del formato antes de persistir en la base de datos.

### Código Fuente
```python
def es_par(n: int) -> bool:
    n = abs(n)
    if n == 0:
        return True  # Caso Base
    return es_impar(n - 1)  # Llama recursivamente a su función homóloga


def es_impar(n: int) -> bool:
    n = abs(n)
    if n == 0:
        return False  # Caso Base
    return es_par(n - 1)   # Llama de vuelta a es_par
```

- **Complejidad:** Temporal $\mathcal{O}(N)$ y Espacial $\mathcal{O}(N)$ de acuerdo al valor numérico evaluado.
