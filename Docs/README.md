# 📚 Centro de Documentación de RutaByte

¡Bienvenido al centro de documentación oficial de **RutaByte**! Este espacio ha sido diseñado específicamente para que los nuevos agentes (humanos o de IA) y desarrolladores puedan comprender rápidamente la arquitectura, los módulos de negocio, los algoritmos académicos implementados y las guías de desarrollo del proyecto.

---

## 🗺️ Mapa de Documentación

Para facilitar la navegación, la documentación se ha dividido en cuatro secciones clave. Te recomendamos leerlas en el orden sugerido si eres nuevo en el proyecto:

### 1. 🏗️ [Arquitectura y Estructura](./ARQUITECTURA.md)
*Entiende los cimientos tecnológicos del sistema.*
- Stack tecnológico completo (FastAPI + Vanilla HTML/CSS/JS + SQLite/MySQL).
- Estructura detallada del árbol de directorios del frontend y backend.
- Flujo de autenticación (JWT con firma asimétrica RS256).
- Diseño y modelo físico de la base de datos.

### 2. 💼 [Módulos de Negocio](./MODULOS.md)
*Explora cómo funciona el sistema para cada rol de usuario.*
- **Flujo de Administración:** Sedes, Usuarios, Categorías y Productos.
- **Flujo de Servicio (Mesero):** Mesas en tiempo real y flujo de Pedidos.
- **Flujo de Caja (Cajero):** Pagos, Facturación e Inventario.
- **Flujo de Analítica (Reportes):** Reporte financiero y gráficas de rendimiento.

### 3. 🧠 [Algoritmos e Integración Académica](./ALGORITMOS.md)
*El núcleo algorítmico y matemático del proyecto.*
- **Algoritmo Voraz (Greedy):** Priorización inteligente de abastecimiento de inventario.
- **Algoritmo de la Mochila 0/1 (Knapsack):** Optimización de compras bajo restricción presupuestaria con Programación Dinámica.
- **Recursividad Simple:** Sumatoria recursiva de ventas.
- **Recursividad Múltiple:** Simulación de crecimiento de negocio mediante Fibonacci.
- **Recursividad Anidada:** Procesamiento y aplanado recursivo del catálogo de categorías.
- **Recursividad Cruzada / Indirecta:** Validación cruzada en la parametrización de mesas (`es_par` / `es_impar`).

### 4. 🚀 [Guía de Desarrollo y Despliegue](./GUIA_DESARROLLO.md)
*Instrucciones paso a paso para comenzar a codificar.*
- Configuración de entornos de desarrollo (Python virtual env, dependencias).
- Inicialización y sembrado de la base de datos (seeders).
- Ejecución local del backend (Uvicorn) y frontend (servidor estático).
- Suite de pruebas unitarias (`pytest`).
- Estándares de desarrollo y guía para añadir nuevas funcionalidades.

---

## 🖼️ Modelo Físico de Base de Datos

El diseño de la base de datos relacional está documentado visualmente. Puedes consultar los archivos directamente en:
- Diagrama en formato de imagen: [Modelo Fisico.png](./ModeloFisico/Modelo%20Fisico.png)
- Archivo editable de Draw.io: [ModeloFisicoRutaByte.drawio](./ModeloFisico/ModeloFisicoRutaByte.drawio)

---

## 💡 Consejos para Nuevos Agentes
1. **Analiza el Backend Primero:** Comienza revisando `backend-fastapi/app/main.py` y `app/api/routes.py` para entender la exposición de los endpoints.
2. **Revisa la Seguridad:** La autenticación utiliza dependencias de FastAPI basadas en roles (ej. `get_current_admin`, `get_current_cajero`, `get_current_user`). Asegúrate de inyectar las cabeceras JWT en tus pruebas.
3. **El Entorno de Datos:** Por defecto, el backend levantará una base de datos SQLite en `backend-fastapi/routabyte.db`. Sin embargo, el esquema principal es 100% compatible con MySQL. Revisa el archivo `.env` para cambiar de motor.
4. **Mantenimiento de los Algoritmos:** Todos los algoritmos están consolidados en `backend-fastapi/app/services/algoritmos_service.py` y expuestos de manera integrada en las APIs operativas del sistema. ¡Evita escribir código duplicado!
