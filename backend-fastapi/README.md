# Backend FastAPI Template

## Estructura

- `app/main.py`
- `app/api/routes.py`
- `tests/test_health.py`
- `requirements.txt`
- `.env.example`

## Como ejecutar

1. Crear entorno virtual:

```bash
python -m venv .venv
```

2. Activar entorno virtual:

- Windows PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

3. Instalar dependencias:

```bash
pip install -r requirements.txt
```

4. Ejecutar API:

```bash
uvicorn app.main:app --reload
```

5. Probar endpoint:

- `GET http://127.0.0.1:8000/api/health`

## MySQL y datos iniciales

1. Copia `.env.example` a `.env` y completa tus credenciales de MySQL.
2. Importa [`Data/rutabyte.sql`](C:/Users/juan.chaparro/Documents/GITHUB/uni/RutaByte/Data/rutabyte.sql) en tu servidor MySQL.
3. Ejecuta el seed inicial:

```bash
python scripts/seed_initial_data.py
```

4. Credenciales semilla:

- `admin@rutabyte.local` / `Admin123!`
- `cajero@rutabyte.local` / `Cajero123!`
- `mesero@rutabyte.local` / `Mesero123!`

## Tests

```bash
pytest -q
```
