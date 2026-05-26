from pathlib import Path
import os

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text
from app.db.base import Base
from app.db.session import engine
from app.core.notifications import notification_manager
from app.core.security import decode_and_verify_jwt

Base.metadata.create_all(bind=engine)


def _ensure_sqlite_columns() -> None:
    if not str(engine.url).startswith("sqlite"):
        return
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if "PRODUCTOS" in tables:
        columnas = {col["name"] for col in inspector.get_columns("PRODUCTOS")}
        with engine.begin() as conn:
            if "costo_compra" not in columnas:
                conn.execute(text('ALTER TABLE "PRODUCTOS" ADD COLUMN costo_compra NUMERIC(10, 2) NOT NULL DEFAULT 0'))
            if "umbral_minimo" not in columnas:
                conn.execute(text('ALTER TABLE "PRODUCTOS" ADD COLUMN umbral_minimo INTEGER NOT NULL DEFAULT 5'))
            if "impuesto_iva" not in columnas:
                conn.execute(text('ALTER TABLE "PRODUCTOS" ADD COLUMN impuesto_iva NUMERIC(4, 2) NOT NULL DEFAULT 0'))
    if "INVENTARIO" in tables:
        columnas = {col["name"] for col in inspector.get_columns("INVENTARIO")}
        with engine.begin() as conn:
            if "umbral_minimo" not in columnas:
                conn.execute(text('ALTER TABLE "INVENTARIO" ADD COLUMN umbral_minimo INTEGER NOT NULL DEFAULT 5'))
    if "USUARIOS" in tables:
        columnas = {col["name"] for col in inspector.get_columns("USUARIOS")}
        with engine.begin() as conn:
            if "intentos_fallidos" not in columnas:
                conn.execute(text('ALTER TABLE "USUARIOS" ADD COLUMN intentos_fallidos INTEGER NOT NULL DEFAULT 0'))
            if "bloqueado_hasta" not in columnas:
                conn.execute(text('ALTER TABLE "USUARIOS" ADD COLUMN bloqueado_hasta TIMESTAMP'))
    if "PEDIDOS" in tables:
        columnas = {col["name"] for col in inspector.get_columns("PEDIDOS")}
        with engine.begin() as conn:
            if "descuento" not in columnas:
                conn.execute(text('ALTER TABLE "PEDIDOS" ADD COLUMN descuento NUMERIC(10, 2) NOT NULL DEFAULT 0'))
            if "tipo_descuento" not in columnas:
                conn.execute(text('ALTER TABLE "PEDIDOS" ADD COLUMN tipo_descuento VARCHAR(20)'))
            if "descuento_valor" not in columnas:
                conn.execute(text('ALTER TABLE "PEDIDOS" ADD COLUMN descuento_valor NUMERIC(10, 2) NOT NULL DEFAULT 0'))
            if "descuento_autorizado_por" not in columnas:
                conn.execute(text('ALTER TABLE "PEDIDOS" ADD COLUMN descuento_autorizado_por INTEGER'))
    if "DETALLE_PEDIDOS" in tables:
        columnas = {col["name"] for col in inspector.get_columns("DETALLE_PEDIDOS")}
        with engine.begin() as conn:
            if "cancelado" not in columnas:
                conn.execute(text('ALTER TABLE "DETALLE_PEDIDOS" ADD COLUMN cancelado BOOLEAN NOT NULL DEFAULT 0'))
            if "justificacion_cancelacion" not in columnas:
                conn.execute(text('ALTER TABLE "DETALLE_PEDIDOS" ADD COLUMN justificacion_cancelacion VARCHAR(255)'))
            if "cancelado_por" not in columnas:
                conn.execute(text('ALTER TABLE "DETALLE_PEDIDOS" ADD COLUMN cancelado_por INTEGER'))
            if "precio_base" not in columnas:
                conn.execute(text('ALTER TABLE "DETALLE_PEDIDOS" ADD COLUMN precio_base NUMERIC(10, 2) NOT NULL DEFAULT 0'))
            if "impuesto_iva_total" not in columnas:
                conn.execute(text('ALTER TABLE "DETALLE_PEDIDOS" ADD COLUMN impuesto_iva_total NUMERIC(10, 2) NOT NULL DEFAULT 0'))
    if "PAGOS" in tables:
        columnas = {col["name"] for col in inspector.get_columns("PAGOS")}
        with engine.begin() as conn:
            if "subtotal_base" not in columnas:
                conn.execute(text('ALTER TABLE "PAGOS" ADD COLUMN subtotal_base NUMERIC(10, 2) NOT NULL DEFAULT 0'))
            if "impuesto_total" not in columnas:
                conn.execute(text('ALTER TABLE "PAGOS" ADD COLUMN impuesto_total NUMERIC(10, 2) NOT NULL DEFAULT 0'))


_ensure_sqlite_columns()

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from app.api.auth import router as auth_router
from app.api.routes import router as api_router
from app.api.admin.sedes import router as sedes_admin_router
from app.api.admin.usuarios import router as usuarios_admin_router
from app.api.admin.productos import router as productos_admin_router
from app.api.admin.auditoria import router as auditoria_admin_router
from app.api.cajero.inventario import router as inventario_cajero_router
from app.api.cajero.pagos import router as pagos_cajero_router
from app.api.cajero.turnos import router as turnos_cajero_router
from app.api.mesero.pedidos import router as pedidos_mesero_router
from app.api.reportes import router as reportes_router
from app.api.mesas import router as mesas_router

app = FastAPI(
    title="RutaByte Backend",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure static/uploads exists and mount static files
os.makedirs("static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(api_router)
app.include_router(auth_router)
app.include_router(sedes_admin_router)
app.include_router(usuarios_admin_router)
app.include_router(productos_admin_router)
app.include_router(auditoria_admin_router)
app.include_router(pedidos_mesero_router)
app.include_router(inventario_cajero_router)
app.include_router(pagos_cajero_router)
app.include_router(turnos_cajero_router)
app.include_router(reportes_router)
app.include_router(mesas_router)


@app.websocket("/ws/pedidos")
async def websocket_pedidos(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token")
    role_id = 0
    if token:
        try:
            payload = decode_and_verify_jwt(token)
            role_id = int(payload.get("rol_id", payload.get("role_id", 0)))
        except Exception:
            pass

    await notification_manager.connect(websocket, role_id)
    try:
        while True:
            # Keep the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        notification_manager.disconnect(websocket)


@app.get("/", tags=["root"])
def read_root() -> dict[str, str]:
    return {"message": "RutaByte backend running"}