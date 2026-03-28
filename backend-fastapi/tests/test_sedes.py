from __future__ import annotations

import base64
import hashlib
import hmac
import json
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import ALGORITHM, SECRET_KEY
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.mesa import Mesa
from app.models.rol import Rol
from app.models.usuario import Usuario


engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _build_token(role_id: int = 1) -> str:
    header = {"alg": ALGORITHM, "typ": "JWT"}
    payload = {"sub": "admin@test.com", "role_id": role_id}

    header_segment = _base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_segment = _base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_segment}.{payload_segment}".encode("utf-8")
    signature = hmac.new(SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
    signature_segment = _base64url_encode(signature)
    return f"{header_segment}.{payload_segment}.{signature_segment}"


def _override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db
Base.metadata.create_all(bind=engine)

client = TestClient(app)
admin_headers = {"Authorization": f"Bearer {_build_token()}"}


@pytest.fixture(autouse=True)
def reset_database() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_create_list_and_soft_delete_sede() -> None:
    response = client.post(
        "/admin/sedes",
        headers=admin_headers,
        json={"nombre": "Sede Centro", "direccion": "Calle 123", "ciudad": "Bogota"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["nombre"] == "Sede Centro"
    assert data["activa"] is True

    listado = client.get("/admin/sedes", headers=admin_headers)
    assert listado.status_code == 200
    assert len(listado.json()) == 1

    delete_response = client.delete(f"/admin/sedes/{data['id']}", headers=admin_headers)
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Sede desactivada correctamente"

    listado_final = client.get("/admin/sedes", headers=admin_headers)
    assert listado_final.status_code == 200
    assert listado_final.json() == []


def test_delete_sede_blocked_by_active_mesa() -> None:
    sede_response = client.post(
        "/admin/sedes",
        headers=admin_headers,
        json={"nombre": "Sede Norte"},
    )
    sede_id = sede_response.json()["id"]

    db = TestingSessionLocal()
    try:
        db.add(Mesa(sede_id=sede_id, identificador_mesa="M-01", activa=True))
        db.commit()
    finally:
        db.close()

    delete_response = client.delete(f"/admin/sedes/{sede_id}", headers=admin_headers)
    assert delete_response.status_code == 400
    assert "mesas activas" in delete_response.json()["detail"]


def test_delete_sede_blocked_by_assigned_user() -> None:
    sede_response = client.post(
        "/admin/sedes",
        headers=admin_headers,
        json={"nombre": "Sede Sur"},
    )
    sede_id = sede_response.json()["id"]

    db = TestingSessionLocal()
    try:
        db.add(Rol(id=1, nombre="Administrador"))
        db.add(
            Usuario(
                rol_id=1,
                sede_id=sede_id,
                nombre="Admin RutaByte",
                correo="admin@rutabyte.test",
                hash_contrasena="hash",
            )
        )
        db.commit()
    finally:
        db.close()

    delete_response = client.delete(f"/admin/sedes/{sede_id}", headers=admin_headers)
    assert delete_response.status_code == 400
    assert "usuarios asignados" in delete_response.json()["detail"]
