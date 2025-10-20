from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from .. import crud, models
from ..deps import get_db, require_permissions
from ..schemas import RoleCreate, RoleRead, RoleUpdate
from ..security import Permission

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("/", response_model=List[RoleRead])
async def list_roles(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_db),
    _: models.User = Depends(require_permissions(Permission.MANAGE_ROLES)),
) -> List[models.Role]:
    return list(crud.role.get_roles(session, skip=skip, limit=limit))


@router.post("/", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_in: RoleCreate,
    session: Session = Depends(get_db),
    current_user: models.User = Depends(require_permissions(Permission.MANAGE_ROLES)),
) -> models.Role:
    try:
        role = crud.role.create_role(
            session,
            name=role_in.name,
            description=role_in.description,
            permissions=role_in.permissions,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    crud.audit.create_log(
        session,
        actor_id=current_user.id,
        action="role.created",
        target_type="role",
        target_id=role.id,
        details=f"Created role {role.name}",
    )
    return role


@router.put("/{role_id}", response_model=RoleRead)
async def update_role(
    role_id: int,
    role_in: RoleUpdate,
    session: Session = Depends(get_db),
    current_user: models.User = Depends(require_permissions(Permission.MANAGE_ROLES)),
) -> models.Role:
    role = crud.role.get_role(session, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    updated_role = crud.role.update_role(
        session,
        role,
        description=role_in.description,
        permissions=role_in.permissions,
    )

    crud.audit.create_log(
        session,
        actor_id=current_user.id,
        action="role.updated",
        target_type="role",
        target_id=updated_role.id,
        details=f"Updated role {updated_role.name}",
    )
    return updated_role


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: int,
    session: Session = Depends(get_db),
    current_user: models.User = Depends(require_permissions(Permission.MANAGE_ROLES)),
) -> None:
    role = crud.role.get_role(session, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    crud.role.delete_role(session, role)
    crud.audit.create_log(
        session,
        actor_id=current_user.id,
        action="role.deleted",
        target_type="role",
        target_id=role_id,
        details=f"Deleted role {role.name}",
    )
