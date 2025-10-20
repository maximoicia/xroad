from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from .. import crud, models
from ..deps import get_current_active_user, get_db, require_permissions
from ..schemas import MemberCreate, MemberRead, MemberUpdate
from ..security import Permission

router = APIRouter(prefix="/members", tags=["members"])


@router.get("/", response_model=List[MemberRead])
async def list_members(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_db),
    _: models.User = Depends(require_permissions(Permission.MANAGE_MEMBERS)),
) -> List[models.Member]:
    return list(crud.member.get_members(session, skip=skip, limit=limit))


@router.post("/", response_model=MemberRead, status_code=status.HTTP_201_CREATED)
async def create_member(
    member_in: MemberCreate,
    session: Session = Depends(get_db),
    current_user: models.User = Depends(require_permissions(Permission.MANAGE_MEMBERS)),
) -> models.Member:
    try:
        member = crud.member.create_member(
            session,
            name=member_in.name,
            description=member_in.description,
            api_key=member_in.api_key,
            security_server_ip=member_in.security_server_ip,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    crud.audit.create_log(
        session,
        actor_id=current_user.id,
        action="member.created",
        target_type="member",
        target_id=member.id,
        details=f"Created member {member.name}",
    )
    return member


@router.put("/{member_id}", response_model=MemberRead)
async def update_member(
    member_id: int,
    member_in: MemberUpdate,
    session: Session = Depends(get_db),
    current_user: models.User = Depends(require_permissions(Permission.MANAGE_MEMBERS)),
) -> models.Member:
    member = crud.member.get_member(session, member_id)
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    updated_member = crud.member.update_member(
        session,
        member,
        description=member_in.description,
        api_key=member_in.api_key,
        security_server_ip=member_in.security_server_ip,
    )

    crud.audit.create_log(
        session,
        actor_id=current_user.id,
        action="member.updated",
        target_type="member",
        target_id=updated_member.id,
        details=f"Updated member {updated_member.name}",
    )
    return updated_member


@router.get("/me", response_model=MemberRead)
async def get_current_member(
    session: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
) -> models.Member:
    if not current_user.member_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not linked to a member")

    member = crud.member.get_member(session, current_user.member_id)
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    return member


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_member(
    member_id: int,
    session: Session = Depends(get_db),
    current_user: models.User = Depends(require_permissions(Permission.MANAGE_MEMBERS)),
) -> None:
    member = crud.member.get_member(session, member_id)
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    crud.member.delete_member(session, member)
    crud.audit.create_log(
        session,
        actor_id=current_user.id,
        action="member.deleted",
        target_type="member",
        target_id=member_id,
        details=f"Deleted member {member.name}",
    )
