from __future__ import annotations

from typing import List, Optional, Sequence

from sqlmodel import Session, delete, select

from .. import models


def get_role(session: Session, role_id: int) -> Optional[models.Role]:
    return session.get(models.Role, role_id)


def get_role_by_name(session: Session, name: str) -> Optional[models.Role]:
    statement = select(models.Role).where(models.Role.name == name)
    return session.exec(statement).first()


def get_roles(session: Session, skip: int = 0, limit: int = 100) -> Sequence[models.Role]:
    statement = select(models.Role).offset(skip).limit(limit)
    return session.exec(statement).all()


def create_role(session: Session, name: str, description: Optional[str], permissions: List[str]) -> models.Role:
    if get_role_by_name(session, name):
        raise ValueError("Role already exists")

    role = models.Role(name=name, description=description)
    session.add(role)
    session.flush()

    for perm in permissions:
        session.add(models.RolePermission(role_id=role.id, permission=perm))

    session.commit()
    session.refresh(role)
    return role


def update_role(session: Session, role: models.Role, description: Optional[str], permissions: Optional[List[str]]) -> models.Role:
    if description is not None:
        role.description = description
    session.add(role)

    if permissions is not None:
        session.exec(delete(models.RolePermission).where(models.RolePermission.role_id == role.id))
        session.flush()
        for perm in permissions:
            session.add(models.RolePermission(role_id=role.id, permission=perm))

    session.commit()
    session.refresh(role)
    return role


def delete_role(session: Session, role: models.Role) -> None:
    session.delete(role)
    session.commit()
