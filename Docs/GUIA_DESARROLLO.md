# 🚀 Guía de Desarrollo y Despliegue

¡Bienvenido a la guía de inicio rápido y desarrollo de **RutaByte**! Este documento contiene instrucciones detalladas para instalar el entorno local, inicializar bases de datos, ejecutar pruebas unitarias y extender el sistema con nuevas funcionalidades.

---

## 💻 Requisitos Previos

Asegúrate de tener instalado en tu estación de trabajo:
- **Python 3.10 o superior** (Verificable con `python --version`).
- **Node.js** (Opcional, útil si deseas levantar servidores estáticos ligeros para el frontend).
- **Git** para el control de versiones.
- **MySQL Server 8.0+** (Opcional, solo si deseas probar el sistema con motor de base de datos MySQL en lugar del SQLite embebido por defecto).

---

## 🛠️ Configuración e Instalación del Backend

Sigue estos pasos detallados desde tu terminal para levantar el servidor de desarrollo FastAPI:

### 1. Clonar el repositorio y navegar a la carpeta de backend
```bash
cd RutaByte/backend-fastapi
```

### 2. Crear un entorno virtual de Python
- **En Windows:**
  ```powershell
  python -m venv .venv
  ```
- **En Linux / macOS:**
  ```bash
  python3 -m venv .venv
  ```

### 3. Activar el entorno virtual
- **En Windows (PowerShell):**
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- **En Windows (Command Prompt):**
  ```cmd
  .venv\Scripts\activate.bat
  ```
- **En Linux / macOS:**
  ```bash
  source .venv/bin/activate
  ```

### 4. Instalar las dependencias requeridas
```bash
pip install -r requirements.txt
```

### 5. Configurar las variables de entorno
Copia la plantilla de configuración `.env.example` para crear tu archivo `.env` local:
```bash
cp .env.example .env
```

Abre el archivo `.env` en tu editor de código. Por defecto, si no configuras credenciales de MySQL, el backend utilizará **SQLite** de forma automática, creando un archivo `routabyte.db` en el directorio raíz del backend.

*Ejemplo de configuración para SQLite local:*
```env
APP_ENV=development
APP_NAME=rutabyte-backend

# JWT (Claves asimétricas preconfiguradas para desarrollo en el directorio ./secrets)
JWT_ALGORITHM=RS256
JWT_ACCESS_TOKEN_EXPIRE_HOURS=8
JWT_PRIVATE_KEY_PATH=./secrets/private.pem
JWT_PUBLIC_KEY_PATH=./secrets/public.pem
JWT_SECRET_KEY=change-me-in-production

ADMIN_ROLE_ID=1
```

---

## 🗄️ Inicialización y Sembrado de la Base de Datos

El sistema cuenta con migraciones y semillas automáticas a través de SQLAlchemy ORM.

### Inicialización en SQLite
Al iniciar el servidor FastAPI por primera vez, SQLAlchemy creará automáticamente el archivo de base de datos `routabyte.db` con todas las tablas e índices definidos en la carpeta `app/models/`.

Para poblar la base de datos con los roles iniciales, la sede por defecto y las cuentas de prueba administrativas, ejecuta el script CLI de sembrado:
```bash
python scripts/seed_initial_data.py
```

### Inicialización en MySQL (Opcional)
Si deseas utilizar un servidor MySQL:
1. Crea una base de datos vacía llamada `rutabyte` en tu servidor.
2. Abre el archivo `.env` en el backend y configura las variables de conexión:
   ```env
   DB_HOST=127.0.0.1
   DB_PORT=3306
   DB_NAME=rutabyte
   DB_USER=tu_usuario
   DB_PASSWORD=tu_contrasena
   DATABASE_URL=mysql+pymysql://tu_usuario:tu_contrasena@127.0.0.1:3306/rutabyte
   ```
3. Importa el esquema físico del archivo [`Data/rutabyte.sql`](../Data/rutabyte.sql) en tu servidor MySQL.
4. Ejecuta el script de sembrado de datos iniciales:
   ```bash
   python scripts/seed_initial_data.py
   ```

---

## 🔑 Credenciales Semilla de Prueba

Una vez ejecutados los seeders, dispondrás de las siguientes cuentas preconfiguradas con diferentes roles para testear los flujos completos del sistema:

| Rol | Correo Electrónico | Contraseña | Sede Asignada |
| :--- | :--- | :--- | :--- |
| **Administrador** | `admin@rutabyte.local` | `Admin123!` | Global (Acceso a todas) |
| **Cajero** | `cajero@rutabyte.local` | `Cajero123!` | Sede Principal |
| **Mesero** | `mesero@rutabyte.local` | `Mesero123!` | Sede Principal |

---

## 🚀 Ejecución del Servidor en Local

### Levantar el Backend (FastAPI)
Ejecuta el servidor ASGI de desarrollo con recarga automática activada:
```bash
uvicorn app.main:app --reload
```
- **URL Base:** `http://127.0.0.1:8000`
- **Swagger Interactivo (Prueba de Endpoints):** `http://127.0.0.1:8000/docs`
- **Documentación Redoc alternativa:** `http://127.0.0.1:8000/redoc`

### Levantar el Frontend (HTML Estático)
Dado que el frontend está construido en HTML, CSS y JS tradicional (Vanilla), no requiere compilación previa.
- **Opción Recomendada:** Abre VS Code, instala la extensión **Live Server**, abre el archivo `frontend-vanilla/index.html`, haz clic derecho y selecciona **Open with Live Server**. Esto montará un servidor en `http://127.0.0.1:5500`.
- **Opción Alternativa (Python):** Puedes levantar un servidor de hosting estático rápido desde la consola de Windows/Linux. Navega a `frontend-vanilla/` y ejecuta:
  ```bash
  python -m http.server 5500
  ```
  Luego, ingresa en tu navegador a `http://127.0.0.1:5500`.

---

## 🧪 Ejecución de Pruebas Unitarias

El backend incluye pruebas unitarias construidas sobre la biblioteca `pytest` y clientes de prueba asíncronos (`httpx`).

Asegúrate de tener el entorno virtual activado, navega a `backend-fastapi/` y corre las pruebas con el siguiente comando:
```bash
pytest
```

Para ver la salida limpia y rápida de las pruebas unitarias:
```bash
pytest -q
```

---

## 📝 Estándares de Codificación y Reglas de Desarrollo

Para asegurar que nuevos agentes o desarrolladores mantengan la calidad técnica y la integridad del proyecto, cumple con los siguientes principios al modificar el código:

1. **Persistencia de Documentación y Comentarios:** No elimines ni sobreescribas comentarios o docstrings existentes a menos que la lógica interna del método haya cambiado radicalmente. Valora el contexto histórico del código.
2. **Tipado Estático (Python Type Hints):** Todas las firmas de funciones y métodos del backend deben incluir tipado estático tanto para los parámetros de entrada como para el valor de retorno.
   - *Mal:* `def sumar(a, b): return a + b`
   - *Bien:* `def sumar(a: int, b: int) -> int: return a + b`
3. **Validación de Datos en Pydantic:** Al añadir propiedades a los modelos del sistema, actualiza o crea los esquemas correspondientes en `backend-fastapi/app/schemas/` para garantizar la serialización automática de la API.
4. **Protección de Endpoints con Inyección de Dependencias:** Cualquier API operativa que realice alteraciones en datos o exponga información confidencial debe incorporar obligatoriamente la inyección del usuario actual, limitando por rol cuando corresponda:
   ```python
   from app.dependencies.auth import get_current_admin
   
   @router.post("/nuevo-recurso", dependencies=[Depends(get_current_admin)])
   def crear_recurso():
       ...
   ```
5. **No Duplicar Lógica de Algoritmos:** Si requieres usar lógica matemática u optimización dentro de un nuevo controlador de API, no redeclare el código. Importe los servicios existentes desde `app.services.algoritmos_service`.
