from __future__ import annotations

from typing import Optional, Sequence

from sqlmodel import Session, select

from .. import models


def get_member(session: Session, member_id: int) -> Optional[models.Member]:
    return session.get(models.Member, member_id)


def get_member_by_name(session: Session, name: str) -> Optional[models.Member]:
    statement = select(models.Member).where(models.Member.name == name)
    return session.exec(statement).first()


def get_members(session: Session, skip: int = 0, limit: int = 100) -> Sequence[models.Member]:
    statement = select(models.Member).offset(skip).limit(limit)
    return session.exec(statement).all()


def create_member(session: Session, name: str, description: Optional[str], api_key: Optional[str],
                  security_server_ip: Optional[str]) -> models.Member:
    if get_member_by_name(session, name):
        raise ValueError("Member already exists")

    member = models.Member(
        name=name,
        description=description,
        api_key=api_key,
        security_server_ip=security_server_ip,
    )
    session.add(member)
    session.commit()
    session.refresh(member)
    return member


def update_member(session: Session, member: models.Member, *, description: Optional[str], api_key: Optional[str],
                  security_server_ip: Optional[str]) -> models.Member:
    if description is not None:
        member.description = description
    if api_key is not None:
        member.api_key = api_key
    if security_server_ip is not None:
        member.security_server_ip = security_server_ip

    session.add(member)
    session.commit()
    session.refresh(member)
    return member


def delete_member(session: Session, member: models.Member) -> None:
    session.delete(member)
    session.commit()
