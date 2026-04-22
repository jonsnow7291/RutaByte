from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.base import Base
from app.db.session import engine

Base.metadata.create_all(bind=engine)

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from app.api.auth import router as auth_router
from app.api.routes import router as api_router
from app.api.admin.sedes import router as sedes_admin_router
from app.api.admin.usuarios import router as usuarios_admin_router
from app.api.admin.productos import router as productos_admin_router
from app.api.cajero.inventario import router as inventario_cajero_router
from app.api.cajero.pagos import router as pagos_cajero_router
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

app.include_router(api_router)
app.include_router(auth_router)
app.include_router(sedes_admin_router)
app.include_router(usuarios_admin_router)
app.include_router(productos_admin_router)
app.include_router(pedidos_mesero_router)
app.include_router(inventario_cajero_router)
app.include_router(pagos_cajero_router)
app.include_router(reportes_router)
app.include_router(mesas_router)

@app.get("/", tags=["root"])
def read_root() -> dict[str, str]:
    return {"message": "RutaByte backend running"}