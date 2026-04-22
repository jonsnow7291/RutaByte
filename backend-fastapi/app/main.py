from pathlib import Path
from app.api.admin.mesas import router as mesas_admin_router

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from app.api.auth import router as auth_router
from app.api.routes import router as api_router
from app.api.admin.sedes import router as sedes_admin_router
from app.api.admin.usuarios import router as usuarios_admin_router
from app.api.admin.productos import router as productos_admin_router
from app.api.mesero.pedidos import router as pedidos_mesero_router

app = FastAPI(
    title="Backend FastAPI Template",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],
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
app.include_router(mesas_admin_router)


@app.get("/", tags=["root"])
def read_root() -> dict[str, str]:
    return {"message": "FastAPI template running"}
