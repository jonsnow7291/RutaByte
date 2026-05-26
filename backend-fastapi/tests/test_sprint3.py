from __future__ import annotations

import os
from decimal import Decimal
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_db
from app.models.mesa import Mesa
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.models.sede import Sede
from app.models.categoria import Categoria
from app.models.producto import Producto
from app.models.inventario import Inventario
from app.models.pedido import Pedido
from app.models.detalle_pedido import DetallePedido
from app.models.turno_caja import TurnoCaja
from app.models.pago import Pago

engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


Base.metadata.create_all(bind=engine)

client = TestClient(app)


def _build_token(usuario_id: int = 2, role_id: int = 2, sede_id: int = 1) -> str:
    """Build RS256 token matching security.py signature."""
    return create_access_token({
        "sub": "user@test.com",
        "correo": "user@test.com",
        "usuario_id": usuario_id,
        "rol_id": role_id,
        "role_id": role_id,
        "sede_id": sede_id,
    })


@pytest.fixture(autouse=True)
def reset_database() -> Generator[None, None, None]:
    # Clear and recreate database tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # Set dependency override
    app.dependency_overrides[get_db] = _override_get_db

    # Seed basic seed dependencies
    with TestingSessionLocal() as db:
        # Roles
        admin_rol = Rol(id=1, nombre="ADMIN")
        cajero_rol = Rol(id=2, nombre="CAJERO")
        mesero_rol = Rol(id=3, nombre="MESERO")
        db.add_all([admin_rol, cajero_rol, mesero_rol])

        # Users
        admin_user = Usuario(id=1, nombre="Admin", correo="admin@test.com", hash_contrasena="Hashed123!", rol_id=1, activo=True)
        cajero_user = Usuario(id=2, nombre="Cajero", correo="cajero@test.com", hash_contrasena="Hashed123!", rol_id=2, activo=True)
        db.add_all([admin_user, cajero_user])

        # Sede and Mesa
        sede = Sede(id=1, nombre="Sede Norte", direccion="Calle 100", ciudad="Bogota")
        mesa = Mesa(id=1, sede_id=1, identificador_mesa="Mesa 1", estado="LIBRE")
        db.add_all([sede, mesa])

        db.commit()

    yield
    app.dependency_overrides.clear()


def test_category_management_crud() -> None:
    # 1. Create a category
    admin_token = _build_token(usuario_id=1, role_id=1)
    headers = {"Authorization": f"Bearer {admin_token}"}

    create_res = client.post(
        "/admin/productos/categorias",
        json={"nombre": "Bebidas"},
        headers=headers
    )
    assert create_res.status_code == 201
    cat_id = create_res.json()["id"]
    assert create_res.json()["nombre"] == "Bebidas"

    # 2. Update category name
    update_res = client.put(
        f"/admin/productos/categorias/{cat_id}",
        json={"nombre": "Bebidas Frías"},
        headers=headers
    )
    assert update_res.status_code == 200
    assert update_res.json()["nombre"] == "Bebidas Frías"

    # 3. Soft-delete/deactivate category
    delete_res = client.delete(
        f"/admin/productos/categorias/{cat_id}",
        headers=headers
    )
    assert delete_res.status_code == 200
    assert delete_res.json()["message"] == "Categoria desactivada correctamente"

    # Verify it is no longer listed in active categories
    list_res = client.get("/admin/productos/categorias", headers=headers)
    assert len(list_res.json()) == 0


def test_product_creation_with_tax() -> None:
    admin_token = _build_token(usuario_id=1, role_id=1)
    headers = {"Authorization": f"Bearer {admin_token}"}

    # First create category
    create_cat = client.post("/admin/productos/categorias", json={"nombre": "Comida"}, headers=headers)
    cat_id = create_cat.json()["id"]

    # Create product with 19% IVA
    prod_payload = {
        "categoria_id": cat_id,
        "codigo": "BURGER-01",
        "nombre": "Hamburguesa Doble",
        "descripcion": "Hamburguesa con doble carne y queso",
        "precio": 15000.0,
        "costo_compra": 8000.0,
        "umbral_minimo": 10,
        "impuesto_iva": 19.0,
    }
    prod_res = client.post("/admin/productos", json=prod_payload, headers=headers)
    assert prod_res.status_code == 201
    assert float(prod_res.json()["impuesto_iva"]) == 19.0

    # Update product tax to 8%
    update_payload = {"impuesto_iva": 8.0}
    prod_id = prod_res.json()["id"]
    update_res = client.put(f"/admin/productos/{prod_id}", json=update_payload, headers=headers)
    assert update_res.status_code == 200
    assert float(update_res.json()["impuesto_iva"]) == 8.0


def test_tax_aware_checkout_and_logs() -> None:
    cajero_token = _build_token(usuario_id=2, role_id=2, sede_id=1)
    headers = {"Authorization": f"Bearer {cajero_token}"}

    # 1. Open turn
    apertura_res = client.post(
        "/cajero/turnos/apertura",
        json={"monto_apertura": 100000.0},
        headers=headers
    )
    assert apertura_res.status_code == 201

    # 2. Seed category, product, order, detail in DB
    with TestingSessionLocal() as db:
        # Category and Product
        cat = Categoria(id=1, nombre="Comida", activa=True)
        prod = Producto(id=1, categoria_id=1, codigo="BURGER-01", nombre="Hamburguesa", precio=Decimal("10000.00"), costo_compra=Decimal("5000.00"), impuesto_iva=Decimal("19.00"))
        db.add_all([cat, prod])

        # Active Order (ENTREGADO)
        pedido = Pedido(id=1, mesa_id=1, usuario_id=2, estado="ENTREGADO", descuento=Decimal("1000.00"))
        detalle = DetallePedido(pedido_id=1, producto_id=1, cantidad=2, precio_unitario=Decimal("10000.00"), costo_unitario=Decimal("5000.00"))
        db.add_all([pedido, detalle])

        # Inventory balance
        inv = Inventario(sede_id=1, producto_id=1, stock=10, umbral_minimo=3)
        db.add(inv)

        db.commit()

    # 3. Process checkout payment
    # Price = 2 * 10000 = 20000 base
    # IVA = 20000 * 0.19 = 3800
    # Total before discount = 23800
    # Discount = 1000
    # Total to pay = 22800
    # Ratio = 22800 / 23800 = 0.957983...
    # Expected subtotal_base = 20000 * ratio = 19159.66
    # Expected impuesto_total = 3800 * ratio = 3640.34
    pay_payload = {
        "pedido_id": 1,
        "metodo_pago": "EFECTIVO",
        "monto_efectivo": 22800.00
    }
    pay_res = client.post("/cajero/pagos", json=pay_payload, headers=headers)
    assert pay_res.status_code == 201
    assert float(pay_res.json()["monto_total"]) == 22800.00
    assert float(pay_res.json()["subtotal_base"]) > 0
    assert float(pay_res.json()["impuesto_total"]) > 0
    assert abs((float(pay_res.json()["subtotal_base"]) + float(pay_res.json()["impuesto_total"])) - 22800.00) < 0.01

    # 4. Check active shift transaction logs
    logs_res = client.get("/cajero/turnos/transacciones", headers=headers)
    assert logs_res.status_code == 200
    assert len(logs_res.json()) == 1
    assert logs_res.json()[0]["pedido_id"] == 1
    assert float(logs_res.json()[0]["impuesto_total"]) > 0


def test_background_csv_export() -> None:
    cajero_token = _build_token(usuario_id=2, role_id=2, sede_id=1)
    headers = {"Authorization": f"Bearer {cajero_token}"}

    # Trigger background global report task
    params = {
        "fecha_inicio": "2026-05-26T00:00:00",
        "fecha_fin": "2026-05-26T23:59:59",
        "sede_id": 1
    }
    res = client.post("/reportes/masivos", params=params, headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "processing"
    assert "reporte_masivo_" in res.json()["file_name"]
