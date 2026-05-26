from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.categoria import Categoria
from app.models.detalle_pedido import DetallePedido
from app.models.inventario import Inventario
from app.models.mesa import Mesa
from app.models.pago import Pago
from app.models.pedido import Pedido
from app.models.producto import Producto
from app.models.rol import Rol
from app.models.sede import Sede
from app.models.usuario import Usuario


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


def _build_token(usuario_id: int, role_id: int, sede_id: int | None = None) -> str:
    return create_access_token(
        {
            "sub": f"user-{usuario_id}@test.com",
            "correo": f"user-{usuario_id}@test.com",
            "usuario_id": usuario_id,
            "rol_id": role_id,
            "role_id": role_id,
            "sede_id": sede_id,
        }
    )


@pytest.fixture(autouse=True)
def reset_database() -> Generator[None, None, None]:
    app.dependency_overrides[get_db] = _override_get_db
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        db.add_all(
            [
                Rol(id=1, nombre="ADMIN"),
                Rol(id=2, nombre="CAJERO"),
                Rol(id=3, nombre="MESERO"),
                Sede(id=1, nombre="Sede Norte", direccion="Calle 1", ciudad="Bogota", activa=True),
                Sede(id=2, nombre="Sede Sur", direccion="Calle 2", ciudad="Bogota", activa=True),
                Usuario(id=1, nombre="Admin", correo="admin@test.com", hash_contrasena="hash", rol_id=1, activo=True),
                Usuario(id=2, nombre="Cajero Norte", correo="cajero@test.com", hash_contrasena="hash", rol_id=2, sede_id=1, activo=True),
                Usuario(id=3, nombre="Mesero Norte", correo="mesero@test.com", hash_contrasena="hash", rol_id=3, sede_id=1, activo=True),
                Mesa(id=1, sede_id=1, identificador_mesa="N-01", estado="LIBRE", activa=True),
                Mesa(id=2, sede_id=2, identificador_mesa="S-01", estado="LIBRE", activa=True),
                Categoria(id=1, nombre="Bebidas", activa=True),
                Producto(
                    id=1,
                    categoria_id=1,
                    codigo="CAF-01",
                    nombre="Cafe",
                    precio=Decimal("5000.00"),
                    costo_compra=Decimal("2000.00"),
                    umbral_minimo=5,
                    activo=True,
                ),
                Inventario(id=1, sede_id=1, producto_id=1, stock=10, umbral_minimo=5),
                Inventario(id=2, sede_id=2, producto_id=1, stock=20, umbral_minimo=5),
                Pedido(id=1, mesa_id=1, usuario_id=3, estado="ENTREGADO", descuento=Decimal("0.00")),
                Pedido(id=2, mesa_id=2, usuario_id=3, estado="ENTREGADO", descuento=Decimal("0.00")),
                DetallePedido(pedido_id=1, producto_id=1, cantidad=1, precio_unitario=Decimal("5000.00"), costo_unitario=Decimal("2000.00")),
                DetallePedido(pedido_id=2, producto_id=1, cantidad=1, precio_unitario=Decimal("5000.00"), costo_unitario=Decimal("2000.00")),
                Pago(
                    id=1,
                    pedido_id=1,
                    usuario_id=2,
                    metodo_pago="EFECTIVO",
                    monto_total=Decimal("5000.00"),
                    subtotal_base=Decimal("5000.00"),
                    impuesto_total=Decimal("0.00"),
                    monto_efectivo=Decimal("5000.00"),
                ),
                Pago(
                    id=2,
                    pedido_id=2,
                    usuario_id=2,
                    metodo_pago="EFECTIVO",
                    monto_total=Decimal("5000.00"),
                    subtotal_base=Decimal("5000.00"),
                    impuesto_total=Decimal("0.00"),
                    monto_efectivo=Decimal("5000.00"),
                ),
            ]
        )
        db.commit()

    yield
    app.dependency_overrides.clear()


def _headers(usuario_id: int, role_id: int, sede_id: int | None = None) -> dict[str, str]:
    return {"Authorization": f"Bearer {_build_token(usuario_id, role_id, sede_id)}"}


def test_sedes_y_mesas_se_filtran_por_sede_para_no_admin_y_admin_ve_todas() -> None:
    cajero_headers = _headers(usuario_id=2, role_id=2, sede_id=1)
    admin_headers = _headers(usuario_id=1, role_id=1)

    sedes_cajero = client.get("/api/sedes", headers=cajero_headers)
    assert sedes_cajero.status_code == 200
    assert [sede["id"] for sede in sedes_cajero.json()] == [1]

    mesas_cajero = client.get("/api/mesas", headers=cajero_headers)
    assert mesas_cajero.status_code == 200
    assert [mesa["sede_id"] for mesa in mesas_cajero.json()] == [1]

    sedes_admin = client.get("/api/sedes", headers=admin_headers)
    assert sedes_admin.status_code == 200
    assert {sede["id"] for sede in sedes_admin.json()} == {1, 2}

    mesas_admin = client.get("/api/mesas", headers=admin_headers)
    assert mesas_admin.status_code == 200
    assert {mesa["sede_id"] for mesa in mesas_admin.json()} == {1, 2}


def test_mesero_no_ve_ni_opera_pedidos_de_otra_sede_y_admin_ve_todos() -> None:
    mesero_headers = _headers(usuario_id=3, role_id=3, sede_id=1)
    admin_headers = _headers(usuario_id=1, role_id=1)

    pedidos_mesero = client.get("/mesero/pedidos", headers=mesero_headers)
    assert pedidos_mesero.status_code == 200
    assert [pedido["mesa_id"] for pedido in pedidos_mesero.json()] == [1]

    pedido_otra_sede = client.get("/mesero/pedidos/2", headers=mesero_headers)
    assert pedido_otra_sede.status_code == 403

    crear_en_otra_sede = client.post(
        "/mesero/pedidos",
        headers=mesero_headers,
        json={"mesa_id": 2, "items": [{"producto_id": 1, "cantidad": 1}]},
    )
    assert crear_en_otra_sede.status_code == 403

    pedidos_admin = client.get("/mesero/pedidos", headers=admin_headers)
    assert pedidos_admin.status_code == 200
    assert {pedido["mesa_id"] for pedido in pedidos_admin.json()} == {1, 2}


def test_cajero_solo_ve_inventario_y_pagos_de_su_sede_aunque_pida_otra() -> None:
    cajero_headers = _headers(usuario_id=2, role_id=2, sede_id=1)

    inventario = client.get("/cajero/inventario?sede_id=2", headers=cajero_headers)
    assert inventario.status_code == 200
    assert [item["sede_id"] for item in inventario.json()] == [1]
    assert [item["stock"] for item in inventario.json()] == [10]

    pendientes = client.get("/cajero/pagos/pendientes", headers=cajero_headers)
    assert pendientes.status_code == 200
    assert [pedido["sede_id"] for pedido in pendientes.json()] == [1]

    pagos = client.get("/cajero/pagos", headers=cajero_headers)
    assert pagos.status_code == 200
    assert [pago["sede_id"] for pago in pagos.json()] == [1]


def test_admin_puede_consultar_datos_de_todas_las_sedes_en_vistas_globales() -> None:
    admin_headers = _headers(usuario_id=1, role_id=1)
    params = {
        "fecha_inicio": datetime(2000, 1, 1).isoformat(),
        "fecha_fin": datetime(2100, 1, 1).isoformat(),
    }

    pedidos = client.get("/mesero/pedidos", headers=admin_headers)
    assert pedidos.status_code == 200
    assert {pedido["mesa_id"] for pedido in pedidos.json()} == {1, 2}

    pagos = client.get("/cajero/pagos", headers=admin_headers)
    assert pagos.status_code == 200
    assert {pago["sede_id"] for pago in pagos.json()} == {1, 2}

    reportes = client.get("/reportes/ventas", headers=admin_headers, params=params)
    assert reportes.status_code == 200
    assert {fila["sede_id"] for fila in reportes.json()} == {1, 2}


def test_reportes_ignoran_sede_query_de_otra_sede_para_cajero() -> None:
    cajero_headers = _headers(usuario_id=2, role_id=2, sede_id=1)
    params = {
        "fecha_inicio": datetime(2000, 1, 1).isoformat(),
        "fecha_fin": datetime(2100, 1, 1).isoformat(),
        "sede_id": 2,
    }

    reportes = client.get("/reportes/ventas", headers=cajero_headers, params=params)
    assert reportes.status_code == 200
    assert [fila["sede_id"] for fila in reportes.json()] == [1]