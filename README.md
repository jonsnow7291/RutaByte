# 📦 RutaByte - Sistema Integral de Gestión para Restaurantes y Almacenes

¡Bienvenido a **RutaByte**! Este es un proyecto de software de tipo **Fullstack** diseñado para la gestión comercial, control de almacenes, comandas en tiempo real, facturación y análisis inteligente de negocios para restaurantes y establecimientos comerciales con múltiples sucursales (sedes). 

El proyecto combina flujos operativos reales con la integración práctica y académica de **6 algoritmos matemáticos y computacionales clásicos** (voraces, programación dinámica y recursividad en todas sus variantes).

---

## 🚀 Inicio Rápido de 3 Pasos

Para levantar el proyecto en menos de 5 minutos:

1. **Configurar el Backend:**
   ```bash
   cd backend-fastapi
   python -m venv .venv
   # Activa tu entorno virtual (.venv\Scripts\Activate.ps1 en Windows o source .venv/bin/activate en Linux)
   pip install -r requirements.txt
   cp .env.example .env
   python scripts/seed_initial_data.py
   uvicorn app.main:app --reload
   ```
   *Nota: Por defecto, el backend creará y utilizará una base de datos SQLite embebida llamada `routabyte.db`.*

2. **Abrir el Frontend:**
   Abre [`frontend-vanilla/index.html`](./frontend-vanilla/index.html) en tu navegador. Puedes utilizar la extensión **Live Server** de VS Code o levantar un servidor estático rápido con Python:
   ```bash
   cd ../frontend-vanilla
   python -m http.server 5500
   ```
   Luego ingresa a `http://127.0.0.1:5500`.

3. **Iniciar Sesión:**
   Utiliza cualquiera de las siguientes credenciales semilla para explorar la aplicación según el rol:
   - **Administrador:** `admin@rutabyte.local` / `Admin123!`
   - **Cajero:** `cajero@rutabyte.local` / `Cajero123!`
   - **Mesero:** `mesero@rutabyte.local` / `Mesero123!`

---

## 📚 Documentación Completa del Proyecto

Para facilitar el onboarding de nuevos desarrolladores y agentes de IA, hemos construido un **Centro de Documentación Exhaustivo** dentro de la carpeta [`Docs/`](./Docs). Te invitamos a leer las guías completas:

- 🗺️ **[Índice del Centro de Documentación](./Docs/README.md):** Mapa general de navegación del contenido técnico.
- 🏗️ **[Arquitectura y Estructura](./Docs/ARQUITECTURA.md):** Stack de tecnologías, estructura física de carpetas del proyecto, modelo entidad-relación de la base de datos y esquema de seguridad JWT RS256.
- 💼 **[Módulos y Reglas de Negocio](./Docs/MODULOS.md):** Detalle de los flujos de Autenticación, Ventas, Control de Mesas, Pedidos (Comanda), Inventario en Sede, Cobros en Caja y Reportes Financieros.
- 🧠 **[Guía de Algoritmos Académicos](./Docs/ALGORITMOS.md):** Explicación teórica, análisis Big O y fragmentos de código de la integración de algoritmos Voraces, Mochila 0/1 con Programación Dinámica y los 4 tipos de Recursión.
- 🛠️ **[Guía del Desarrollador](./Docs/GUIA_DESARROLLO.md):** Manual completo de instalación, sembrado de datos, suite de pruebas automatizadas con `pytest` y estándares para nuevos colaboradores.

---

## ⚙️ Características Destacadas
- **Arquitectura Cliente-Servidor:** Desacoplada e interactiva por medio de APIs REST (FastAPI + JSON).
- **Seguridad Garantizada:** Contraseñas hasheadas con Bcrypt y tokens de acceso JWT asimétricos con algoritmo RS256.
- **Doble Compatibilidad de Motor:** Soporte nativo y autodetectable para **SQLite** (desarrollo rápido sin dependencias de hardware) y **MySQL** (entorno corporativo robusto).
- **Integridad de Datos Contables:** Los costos e ingresos se congelan en los detalles de las comandas para evitar desajustes históricos de inflación o alteraciones en las existencias físicas de almacén.
- **Gráficos e Indicadores:** Reportes financieros exportables a CSV y dashboards interactivos en tiempo real.