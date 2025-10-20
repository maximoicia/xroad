from __future__ import annotations

from typing import Optional, Sequence

from sqlmodel import Session, select

from .. import models


def create_log(session: Session, *, actor_id: Optional[int], action: str, target_type: str,
               target_id: Optional[int], details: Optional[str] = None) -> models.AuditLog:
    log_entry = models.AuditLog(
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
    )
    session.add(log_entry)
    session.commit()
    session.refresh(log_entry)
    return log_entry


def list_logs(session: Session, skip: int = 0, limit: int = 100) -> Sequence[models.AuditLog]:
    statement = (
        select(models.AuditLog)
        .order_by(models.AuditLog.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return session.exec(statement).all()
