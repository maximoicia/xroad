from __future__ import annotations

from typing import List, Optional, Sequence

from sqlmodel import Session, delete, select

from .. import models
from ..security import get_password_hash


def get_user_by_username(session: Session, username: str) -> Optional[models.User]:
    statement = select(models.User).where(models.User.username == username)
    return session.exec(statement).first()


def get_user_by_email(session: Session, email: str) -> Optional[models.User]:
    statement = select(models.User).where(models.User.email == email)
    return session.exec(statement).first()


def get_user(session: Session, user_id: int) -> Optional[models.User]:
    return session.get(models.User, user_id)


def get_users(session: Session, skip: int = 0, limit: int = 100) -> Sequence[models.User]:
    statement = select(models.User).offset(skip).limit(limit)
    return session.exec(statement).all()


def create_user(session: Session, *, username: str, email: str, password: str, full_name: Optional[str],
                member_id: Optional[int], role_ids: Optional[List[int]] = None) -> models.User:
    if get_user_by_username(session, username):
        raise ValueError("Username already exists")
    if get_user_by_email(session, email):
        raise ValueError("Email already exists")

    db_user = models.User(
        username=username,
        email=email,
        full_name=full_name,
        hashed_password=get_password_hash(password),
        member_id=member_id,
    )
    session.add(db_user)
    session.flush()

    if role_ids:
        for role_id in role_ids:
            session.add(models.UserRoleLink(user_id=db_user.id, role_id=role_id))

    session.commit()
    session.refresh(db_user)
    return db_user


def update_user(session: Session, db_user: models.User, *, email: Optional[str] = None,
                full_name: Optional[str] = None, is_active: Optional[bool] = None,
                password: Optional[str] = None, member_id: Optional[int] = None,
                role_ids: Optional[List[int]] = None) -> models.User:
    if email and email != db_user.email:
        existing = get_user_by_email(session, email)
        if existing and existing.id != db_user.id:
            raise ValueError("Email already exists")
        db_user.email = email
    if full_name is not None:
        db_user.full_name = full_name
    if is_active is not None:
        db_user.is_active = is_active
    if password:
        db_user.hashed_password = get_password_hash(password)
    if member_id is not None:
        db_user.member_id = member_id

    if role_ids is not None:
        session.exec(delete(models.UserRoleLink).where(models.UserRoleLink.user_id == db_user.id))
        session.flush()
        for role_id in role_ids:
            session.add(models.UserRoleLink(user_id=db_user.id, role_id=role_id))

    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_permissions(session: Session, user: models.User) -> List[str]:
    statement = (
        select(models.RolePermission.permission)
        .join(models.RolePermission.role)
        .join(models.UserRoleLink, models.UserRoleLink.role_id == models.RolePermission.role_id)
        .where(models.UserRoleLink.user_id == user.id)
    )
    return session.exec(statement).all()
