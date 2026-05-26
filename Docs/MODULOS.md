# 💼 Módulos de Negocio y Flujos Funcionales

Esta sección profundiza en los diferentes módulos operativos de **RutaByte**, detallando las reglas de negocio, los endpoints involucrados y el comportamiento del frontend para cada rol del sistema.

---

## 🔑 1. Autenticación y Seguridad

El ciclo de vida del usuario dentro de la plataforma está gobernado por el módulo de autenticación.

### Flujo de Login y Persistencia
1. El usuario introduce sus credenciales en `login.html`.
2. El script `js/auth.js` envía una solicitud `POST` a `/auth/login` con las credenciales cifradas en texto plano (el backend las comparará con el hash de Bcrypt).
3. Si es exitoso, el backend emite un token JWT que el frontend almacena en el `localStorage` del navegador bajo la llave `token`.
4. El token se analiza localmente (se decodifica el payload en Base64) para extraer datos rápidos como el `nombre`, `rol_id` y `sede_id` del usuario, permitiendo personalizar la interfaz gráfica de inmediato.
5. Cada petición fetch subsiguiente adjunta la cabecera HTTP:
   `Authorization: Bearer <token>`
6. **Recuperación de Contraseña:** El endpoint `POST /auth/recuperar-password` genera un token temporal (`TOKEN_RECUPERACION`) en la base de datos asociado al correo del usuario y simula el envío de un correo con un enlace seguro a `recuperar.html` para reestablecer la credencial.

---

## 🏢 2. Gestión de Sedes (Administrador)

Permite la administración de las diferentes ubicaciones físicas o sucursales del negocio.

### Reglas de Negocio
- Únicamente los usuarios con rol **ADMIN** pueden crear, editar o desactivar sedes.
- El endpoint `GET /api/sedes` (público para autenticados) tiene filtrado implícito:
  - Si el usuario logueado es **ADMIN**, el backend retorna la lista completa de todas las sedes activas en el sistema.
  - Si el usuario es **CAJERO** o **MESERO**, el backend filtra automáticamente la consulta y **únicamente** devuelve la sede que dicho usuario tiene asignada en su perfil. Esto evita fugas de información inter-sucursal.
- Desactivar una sede (`DELETE /admin/sedes/{id}`) no la elimina físicamente para preservar la integridad histórica de ventas, sino que cambia su estado `activa` a `FALSE`.

---

## 👥 3. Administración de Usuarios y Personal (Administrador)

Gestiona a los colaboradores del negocio, sus roles y sus asignaciones geográficas.

### Reglas de Negocio
- **Roles del Sistema:**
  1. `ADMIN` (ID 1): Control total del sistema, configuración, catálogo, mesas y reportería ejecutiva global.
  2. `CAJERO` (ID 2): Encargado del cobro de pedidos, facturación, y administración física del inventario de su sede asignada.
  3. `MESERO` (ID 3): Encargado de la atención en salón, asignación de mesas y toma de pedidos en su sede asignada.
- Al crear o modificar un usuario (`POST` / `PUT` a `/admin/usuarios`), el administrador debe especificar a qué sede física pertenece el colaborador (excepto para administradores globales que pueden tener `sede_id` nulo).
- Las contraseñas se almacenan mediante el algoritmo seguro hash **Bcrypt** implementado en `backend-fastapi/app/core/security.py`.

---

## 🏷️ 4. Catálogo de Categorías y Productos (Administrador)

Administra los productos de consumo y los insumos del negocio.

### Reglas de Negocio
- Los productos pertenecen obligatoriamente a una categoría de catálogo (ej. "Bebidas", "Comidas Rápidas").
- **Historial de Precios:** Cada vez que un administrador actualiza el precio de venta de un producto, el sistema genera automáticamente un registro en la tabla `HISTORIAL_PRECIOS`, almacenando el precio anterior, el nuevo precio, la fecha exacta del cambio y el identificador del administrador que ejecutó la acción.
- **Costo de Compra (`costo_compra`):** Es un campo obligatorio y representa el coste de adquisición del insumo. Sirve de base matemática para calcular la ganancia (`ganancia = precio_venta - costo_compra`), que es utilizada por los algoritmos de optimización de inventario.
- **Jerarquía de Categorías:** El endpoint `GET /admin/productos/categorias/arbol` estructura de manera jerárquica las categorías activas junto a sus productos y aplica **Recursividad Anidada** para aplanar los nombres para auditoría.

---

## 🍽️ 5. Mesas y Pedidos (Flujo del Mesero)

Este módulo representa el motor operativo diario de atención al cliente en el restaurante.

```text
[Mesero]              [Mesero]              [Mesero]              [Cajero]
   │                     │                     │                     │
 Crea Mesa  ──────> Abre Pedido ──────> Agrega Detalles ────> Procesa Pago
 (Identificador)    (Estado:            (Costo y precio      (Estado Pedido ->
                    EN_PREPARACION)      unitario se         ENTREGADO y
                                         congelan)           Mesa -> LIBRE)
```

### Flujo Operativo:
1. **Asignación de Mesa:** El mesero visualiza la sala interactiva en `mesas.html`. Las mesas tienen dos estados físicos: `LIBRE` u `OCUPADA`.
2. **Apertura del Pedido:** Al seleccionar una mesa libre, el mesero puede abrir un nuevo pedido mediante `POST /mesero/pedidos`. Esto cambia el estado de la mesa a `OCUPADA`.
3. **Adición de Ítems (Comanda):** El mesero agrega productos y cantidades al pedido. El sistema calcula en tiempo real los totales. Al guardar, el backend registra los detalles en la tabla `DETALLE_PEDIDOS`.
   - *Nota de Diseño Crítica:* Al insertar un detalle de pedido, el backend lee el costo de compra y el precio de venta actuales del catálogo y los guarda físicamente en la fila del detalle. Si en el futuro el administrador cambia el precio de un producto, las facturas previas no sufrirán alteraciones y el reporte histórico de ganancias seguirá siendo 100% exacto.
4. **Estados del Pedido:** Un pedido transita por los siguientes estados:
   - `EN_PREPARACION`: El pedido se está procesando en la cocina.
   - `LISTO`: La comida está lista para ser servida.
   - `ENTREGADO`: El pedido ha sido servido al cliente y está listo para ser facturado en caja.

---

## 📦 6. Inventario y Almacén (Flujo del Cajero)

El cajero de cada sede es responsable de controlar las existencias de mercancía o insumos.

### Reglas de Negocio
- Cada sede física posee su propio stock de inventario independiente (`INVENTARIO`).
- Al crear un producto nuevo en el sistema, no se crea stock automáticamente. El cajero debe registrar una entrada física de almacén (`POST /cajero/inventario/entradas`) especificando la cantidad ingresada y el motivo (ej. "Compra a proveedor", "Ajuste de inventario").
- **Kardex / Movimientos:** Cada entrada o salida de inventario genera una fila inmutable en `MOVIMIENTOS_INVENTARIO`, la cual está vinculada al usuario cajero que firmó la operación.
- **Descarga de Stock por Venta:** Cuando un pedido es pagado y finalizado en el módulo de caja, el sistema descuenta de forma automática y atómica las existencias físicas en la sede correspondiente para cada producto consumido en el pedido.
- **Alertas de Stock Bajo:** Si el stock de un producto cae por debajo del `umbral_minimo` configurado para dicho producto, el sistema genera alertas visuales en el panel de inventario y lo clasifica para reabastecimiento urgente.
- **Integración de Algoritmos:** El módulo de inventario incorpora las sugerencias inteligentes de reabastecimiento:
  - **Algoritmo Voraz:** Sugiere una lista de compras priorizando productos con stock crítico (bajo umbral) y alto margen de ganancia.
  - **Algoritmo de la Mochila:** Optimiza la combinación de productos a comprar con base en un presupuesto limitado definido por el cajero.

---

## 💳 7. Procesamiento de Pagos y Facturación (Flujo del Cajero)

El módulo que cierra el ciclo comercial y consolida los ingresos económicos del negocio.

### Reglas de Negocio
- El cajero accede a `pagos.html`, visualiza todos los pedidos activos de su sede que se encuentran en estado `ENTREGADO` y que no han sido saldados.
- El cajero selecciona el método de pago:
  - `EFECTIVO`
  - `TARJETA`
  - `TRANSFERENCIA`
- Al procesar la transacción (`POST /cajero/pagos`), el backend:
  1. Crea un registro en la tabla `PAGOS` vinculando el ID del pedido y la forma de pago.
  2. Dispara la deducción de inventario de los productos consumidos en la sede.
  3. Modifica el estado del pedido a `ENTREGADO` (completado y facturado).
  4. Modifica de forma automática el estado de la mesa vinculada al pedido a `LIBRE` para que pueda ser utilizada por nuevos comensales.
- Permite la visualización de una factura simple en formato ticket térmico lista para impresión física.

---

## 📊 8. Reportes y Business Intelligence (Administrador / Cajero)

Permite la auditoría financiera y el análisis de rendimiento de las sedes.

### Funcionalidades Core
- **Reporte Ejecutivo de Ventas:** Filtra todas las transacciones saldadas del sistema por un rango de fechas y una sede en particular. Calcula las métricas clave:
  - **Venta Bruta:** Ingresos totales de ventas de los productos facturados.
  - **Costo Operativo:** Costo total de adquisición de los productos vendidos.
  - **Ganancia Real (Margen Neto):** `Venta Bruta - Costo Operativo`.
- **Exportación de Datos:** Permite descargar el reporte financiero completo directamente en formato `CSV` estructurado (`GET /reportes/ventas/export/csv`) para su posterior manipulación en hojas de cálculo externas.
- **Cálculo de Totales por Recursividad:** El endpoint `/reportes/ventas/resumen-recursivo` procesa matemáticamente los totales del reporte utilizando **Recursividad Simple** (sumatorias recursivas en memoria) y calcula un escenario de crecimiento de ventas con **Recursividad Múltiple** (Fibonacci).
- **Dashboard Gráfico:** El endpoint `/reportes/ventas-graficas` agrupa la información financiera y de existencias, entregando datos formateados para que la interfaz dibuje gráficos dinámicos (utilizando librerías de JS como Chart.js) que muestran:
  - Ventas por día (Tendencia).
  - Productos más vendidos (Top 10 volumen).
  - Productos más rentables (Top 10 ganancias).
  - Ventas consolidadas por sede.
  - Métodos de pago más utilizados.
  - Listado de alertas por stock crítico.
