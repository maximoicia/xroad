from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session

from .. import crud, models
from ..deps import get_db, require_permissions
from ..schemas import AuditLogRead
from ..security import Permission

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/", response_model=List[AuditLogRead])
async def list_audit_logs(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_db),
    _: models.User = Depends(require_permissions(Permission.VIEW_AUDIT_LOGS)),
) -> List[models.AuditLog]:
    return list(crud.audit.list_logs(session, skip=skip, limit=limit))
