from __future__ import annotations

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
from app.models.movimiento_inventario import MovimientoInventario
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
    app.dependency_overrides[get_db] = _override_get_db
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


def _setup_basic_data(db: Session) -> dict:
    # Sede
    sede = Sede(nombre="Sede Norte", direccion="Calle 1", ciudad="Bogota", activa=True)
    db.add(sede)
    db.flush()

    # Roles
    rol_admin = Rol(id=1, nombre="ADMINISTRADOR")
    rol_cajero = Rol(id=2, nombre="CAJERO")
    rol_mesero = Rol(id=3, nombre="MESERO")
    db.add_all([rol_admin, rol_cajero, rol_mesero])
    db.flush()

    # Users (pwd for admin: 'adminpwd' -> mocked bcrypt or we don't care, we can use passlib to hash it)
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    admin_hash = pwd_context.hash("admin123")

    admin = Usuario(rol_id=1, sede_id=sede.id, nombre="Admin User", correo="admin@test.com", hash_contrasena=admin_hash, activo=True)
    cajero = Usuario(rol_id=2, sede_id=sede.id, nombre="Cajero User", correo="cajero@test.com", hash_contrasena="hash", activo=True)
    mesero = Usuario(rol_id=3, sede_id=sede.id, nombre="Mesero User", correo="mesero@test.com", hash_contrasena="hash", activo=True)
    db.add_all([admin, cajero, mesero])
    db.flush()

    # Mesas
    mesa1 = Mesa(sede_id=sede.id, identificador_mesa="Mesa 1", activa=True, estado="LIBRE")
    mesa2 = Mesa(sede_id=sede.id, identificador_mesa="Mesa 2", activa=True, estado="LIBRE")
    db.add_all([mesa1, mesa2])
    db.flush()

    # Categoria
    cat = Categoria(nombre="Comida", activa=True)
    db.add(cat)
    db.flush()

    # Productos
    prod1 = Producto(categoria_id=cat.id, nombre="Hamburguesa", descripcion="Hamburguesa de res", precio=Decimal("20.00"), costo_compra=Decimal("8.00"), umbral_minimo=5, activo=True, codigo="HAM-01")
    prod2 = Producto(categoria_id=cat.id, nombre="Gaseosa", descripcion="Coca Cola", precio=Decimal("5.00"), costo_compra=Decimal("2.00"), umbral_minimo=5, activo=True, codigo="GAS-01")
    db.add_all([prod1, prod2])
    db.flush()

    # Inventario
    inv1 = Inventario(sede_id=sede.id, producto_id=prod1.id, stock=10, umbral_minimo=5)
    inv2 = Inventario(sede_id=sede.id, producto_id=prod2.id, stock=3, umbral_minimo=5)
    db.add_all([inv1, inv2])
    db.flush()

    db.commit()

    return {
        "sede_id": sede.id,
        "admin_id": admin.id,
        "cajero_id": cajero.id,
        "mesero_id": mesero.id,
        "mesa1_id": mesa1.id,
        "mesa2_id": mesa2.id,
        "prod1_id": prod1.id,
        "prod2_id": prod2.id,
        "inv1_id": inv1.id,
        "inv2_id": inv2.id,
    }


def test_shift_lifecycle_and_discrepancy() -> None:
    db = TestingSessionLocal()
    data = _setup_basic_data(db)
    token = _build_token(usuario_id=data["cajero_id"], role_id=2, sede_id=data["sede_id"])
    headers = {"Authorization": f"Bearer {token}"}

    # Verify no active shift
    response = client.get("/cajero/turnos/activo", headers=headers)
    assert response.status_code == 404

    # Open shift
    response = client.post("/cajero/turnos/apertura", headers=headers, json={"monto_apertura": 100.00})
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["monto_apertura"] == "100.00"
    assert res_data["estado"] == "ABIERTO"
    shift_id = res_data["id"]

    # Active shift exists now
    response = client.get("/cajero/turnos/activo", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == shift_id

    # Try to close with discrepancy and NO justification
    response = client.post("/cajero/turnos/cierre", headers=headers, json={
        "monto_cierre_real": 120.00,  # Expected is 100.00, so we have discrepancy of 20.00
        "justificacion": ""
    })
    assert response.status_code == 400
    assert "justificación" in response.json()["detail"]

    # Close with discrepancy AND justification
    response = client.post("/cajero/turnos/cierre", headers=headers, json={
        "monto_cierre_real": 120.00,
        "justificacion": "Sobrante de caja no identificado"
    })
    assert response.status_code == 200
    res_close = response.json()
    assert res_close["estado"] == "CERRADO"
    assert res_close["monto_cierre_real"] == "120.00"
    assert res_close["monto_cierre_esperado"] == "100.00"
    assert res_close["justificacion"] == "Sobrante de caja no identificado"

    db.close()


def test_payment_blocks_if_no_shift() -> None:
    db = TestingSessionLocal()
    data = _setup_basic_data(db)
    token = _build_token(usuario_id=data["cajero_id"], role_id=2, sede_id=data["sede_id"])
    headers = {"Authorization": f"Bearer {token}"}

    # Create a dummy entregado pedido
    pedido = Pedido(mesa_id=data["mesa1_id"], usuario_id=data["mesero_id"], estado="ENTREGADO")
    pedido.detalles.append(DetallePedido(producto_id=data["prod1_id"], cantidad=2, precio_unitario=Decimal("20.00"), costo_unitario=Decimal("8.00")))
    db.add(pedido)
    db.commit()

    # Try to register payment without open shift
    response = client.post("/cajero/pagos", headers=headers, json={
        "pedido_id": pedido.id,
        "metodo_pago": "EFECTIVO",
        "monto_efectivo": 40.00
    })
    assert response.status_code == 400
    assert "turno de caja abierto" in response.json()["detail"]

    db.close()


def test_item_cancellation_and_transfer() -> None:
    db = TestingSessionLocal()
    data = _setup_basic_data(db)
    token_mesero = _build_token(usuario_id=data["mesero_id"], role_id=3, sede_id=data["sede_id"])
    headers = {"Authorization": f"Bearer {token_mesero}"}

    # Create pedido
    response = client.post("/mesero/pedidos", headers=headers, json={
        "mesa_id": data["mesa1_id"],
        "items": [
            {"producto_id": data["prod1_id"], "cantidad": 2, "notas": "Sin cebolla"},
            {"producto_id": data["prod2_id"], "cantidad": 1, "notas": "Bien helada"},
        ]
    })
    assert response.status_code == 201
    pedido_id = response.json()["id"]
    detalles = response.json()["detalles"]
    detalle_gas_id = [d["id"] for d in detalles if d["producto_id"] == data["prod2_id"]][0]

    # Cancel one item (gaseosa)
    response = client.post(
        f"/mesero/pedidos/{pedido_id}/detalles/{detalle_gas_id}/cancelar",
        headers=headers,
        json={"justificacion": "Cliente cambió de opinión"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Item cancelado correctamente"

    # Verify cancel fields in DB
    db.expire_all()
    det = db.get(DetallePedido, detalle_gas_id)
    assert det.cancelado is True
    assert det.justificacion_cancelacion == "Cliente cambió de opinión"
    assert det.cancelado_por == data["mesero_id"]

    # Transfer Pedido to Mesa 2
    response = client.post(
        f"/mesero/pedidos/{pedido_id}/transferir?mesa_destino_id={data['mesa2_id']}",
        headers=headers
    )
    assert response.status_code == 200
    assert "transferido" in response.json()["message"]

    # Check tables states
    db.expire_all()
    ped = db.get(Pedido, pedido_id)
    assert ped.mesa_id == data["mesa2_id"]
    assert db.get(Mesa, data["mesa1_id"]).estado == "LIBRE"
    assert db.get(Mesa, data["mesa2_id"]).estado == "OCUPADA"

    db.close()


def test_payment_atomic_sync_and_manual_discount() -> None:
    db = TestingSessionLocal()
    data = _setup_basic_data(db)
    token_cajero = _build_token(usuario_id=data["cajero_id"], role_id=2, sede_id=data["sede_id"])
    headers = {"Authorization": f"Bearer {token_cajero}"}

    # Open cashier shift
    client.post("/cajero/turnos/apertura", headers=headers, json={"monto_apertura": 100.00})

    # Create pedido (Hamburguesa x2 (40.00) + Gaseosa x1 (5.00))
    token_mesero = _build_token(usuario_id=data["mesero_id"], role_id=3, sede_id=data["sede_id"])
    headers_mesero = {"Authorization": f"Bearer {token_mesero}"}

    response = client.post("/mesero/pedidos", headers=headers_mesero, json={
        "mesa_id": data["mesa1_id"],
        "items": [
            {"producto_id": data["prod1_id"], "cantidad": 2},
            {"producto_id": data["prod2_id"], "cantidad": 1},
        ]
    })
    pedido_id = response.json()["id"]

    # Advance state to ENTREGADO
    client.patch(f"/mesero/pedidos/{pedido_id}/estado", headers=headers_mesero)
    client.patch(f"/mesero/pedidos/{pedido_id}/estado", headers=headers_mesero)

    # Cancel the gaseosa (item_total will be 40.00)
    detalle_gas_id = [d["id"] for d in response.json()["detalles"] if d["producto_id"] == data["prod2_id"]][0]
    client.post(
        f"/mesero/pedidos/{pedido_id}/detalles/{detalle_gas_id}/cancelar",
        headers=headers_mesero,
        json={"justificacion": "Anulación de prueba"}
    )

    # Apply 10% discount authorized by Admin (hamburger total is 40.00, 10% is 4.00, new total 36.00)
    response = client.post(f"/cajero/pagos/{pedido_id}/descuento", headers=headers, json={
        "tipo_descuento": "PORCENTAJE",
        "descuento_valor": 10.00,
        "admin_username": "admin@test.com",
        "admin_password": "admin123"
    })
    assert response.status_code == 200
    assert response.json()["descuento"] == "4.00"
    assert response.json()["descuento_valor"] == "10.00"

    # Make stock insufficient for Hamburger in inventory (set to 1, we need 2)
    inv = db.get(Inventario, data["inv1_id"])
    inv.stock = 1
    db.commit()

    # Process payment: should FAIL due to insufficient Hamburguer stock, and rollback
    response = client.post("/cajero/pagos", headers=headers, json={
        "pedido_id": pedido_id,
        "metodo_pago": "EFECTIVO",
        "monto_efectivo": 36.00
    })
    assert response.status_code == 400
    assert "insuficiente" in response.json()["detail"]

    # Restore stock
    db.expire_all()
    inv.stock = 10
    db.commit()

    # Process payment: should SUCCEED now
    response = client.post("/cajero/pagos", headers=headers, json={
        "pedido_id": pedido_id,
        "metodo_pago": "EFECTIVO",
        "monto_efectivo": 36.00
    })
    assert response.status_code == 201

    # Check stock was debited atomically
    db.expire_all()
    assert db.get(Inventario, data["inv1_id"]).stock == 8  # 10 - 2 = 8
    # Gaseosa was cancelled, so its stock should NOT be affected
    assert db.get(Inventario, data["inv2_id"]).stock == 3  # remained at 3

    # Check shift expected cash calculation
    response = client.post("/cajero/turnos/cierre", headers=headers, json={
        "monto_cierre_real": 136.00,
        "justificacion": ""
    })
    assert response.status_code == 200
    assert response.json()["monto_cierre_esperado"] == "136.00"  # 100 opening + 36 cash payment

    db.close()


def test_manual_stock_output() -> None:
    db = TestingSessionLocal()
    data = _setup_basic_data(db)
    token = _build_token(usuario_id=data["cajero_id"], role_id=2, sede_id=data["sede_id"])
    headers = {"Authorization": f"Bearer {token}"}

    # Manual stock output of Hamburguesa x3 due to wastage
    response = client.post("/cajero/inventario/salidas", headers=headers, json={
        "producto_id": data["prod1_id"],
        "cantidad": 3,
        "motivo": "Mermas por vencimiento"
    })
    assert response.status_code == 201
    assert response.json()["stock"] == 7  # 10 - 3 = 7

    # Verify audit movement
    db.expire_all()
    inv = db.get(Inventario, data["inv1_id"])
    stmt = select(MovimientoInventario).where(MovimientoInventario.inventario_id == inv.id).order_by(MovimientoInventario.creado_en.desc())
    mov = db.scalar(stmt)
    assert mov.tipo == "SALIDA"
    assert mov.cantidad == 3
    assert mov.stock_anterior == 10
    assert mov.stock_nuevo == 7
    assert mov.motivo == "Mermas por vencimiento"
    assert mov.usuario_id == data["cajero_id"]

    db.close()
