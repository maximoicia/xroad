from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import Session

from .. import crud, models
from ..deps import get_db, require_permissions
from ..schemas import UserCreate, UserRead, UserUpdate
from ..security import Permission

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=List[UserRead])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_db),
    _: models.User = Depends(require_permissions(Permission.MANAGE_USERS)),
) -> List[models.User]:
    return list(crud.user.get_users(session, skip=skip, limit=limit))


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    session: Session = Depends(get_db),
    current_user: models.User = Depends(require_permissions(Permission.MANAGE_USERS)),
) -> models.User:
    try:
        user = crud.user.create_user(
            session,
            username=user_in.username,
            email=user_in.email,
            password=user_in.password,
            full_name=user_in.full_name,
            member_id=user_in.member_id,
            role_ids=user_in.role_ids,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    crud.audit.create_log(
        session,
        actor_id=current_user.id,
        action="user.created",
        target_type="user",
        target_id=user.id,
        details=f"Created user {user.username}",
    )
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    session: Session = Depends(get_db),
    current_user: models.User = Depends(require_permissions(Permission.MANAGE_USERS)),
) -> Response:
    db_user = crud.user.get_user(session, user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    session.delete(db_user)
    session.commit()

    crud.audit.create_log(
        session,
        actor_id=current_user.id,
        action="user.deleted",
        target_type="user",
        target_id=user_id,
        details=f"Deleted user {db_user.username}",
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    session: Session = Depends(get_db),
    current_user: models.User = Depends(require_permissions(Permission.MANAGE_USERS)),
) -> models.User:
    db_user = crud.user.get_user(session, user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    try:
        user = crud.user.update_user(
            session,
            db_user,
            email=user_in.email,
            full_name=user_in.full_name,
            is_active=user_in.is_active,
            password=user_in.password,
            member_id=user_in.member_id,
            role_ids=user_in.role_ids,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    crud.audit.create_log(
        session,
        actor_id=current_user.id,
        action="user.updated",
        target_type="user",
        target_id=user.id,
        details=f"Updated user {user.username}",
    )
    return user
