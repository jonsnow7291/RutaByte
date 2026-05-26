from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_admin
from app.db.session import get_db
from app.models.auditoria import RegistroAuditoria
from app.schemas.auditoria import RegistroAuditoriaResponse

router = APIRouter(
    prefix="/admin/auditoria",
    tags=["admin-auditoria"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("", response_model=list[RegistroAuditoriaResponse])
def listar_auditoria(
    usuario_id: int | None = None,
    tipo_evento: str | None = None,
    fecha_inicio: datetime | None = None,
    fecha_fin: datetime | None = None,
    db: Session = Depends(get_db),
) -> list[RegistroAuditoria]:
    stmt = select(RegistroAuditoria)
    filters = []

    if usuario_id is not None:
        filters.append(RegistroAuditoria.usuario_id == usuario_id)

    if tipo_evento is not None and tipo_evento.strip():
        filters.append(RegistroAuditoria.tipo_evento == tipo_evento.strip())

    if fecha_inicio is not None:
        filters.append(RegistroAuditoria.creado_en >= fecha_inicio)

    if fecha_fin is not None:
        filters.append(RegistroAuditoria.creado_en <= fecha_fin)

    if filters:
        stmt = stmt.where(and_(*filters))

    stmt = stmt.order_by(RegistroAuditoria.creado_en.desc())
    return list(db.scalars(stmt).all())
