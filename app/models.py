from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class RolePermission(SQLModel, table=True):
    """Association between roles and permissions."""

    role_id: Optional[int] = Field(default=None, foreign_key="role.id", primary_key=True)
    permission: str = Field(primary_key=True, index=True)

    role: "Role" = Relationship(back_populates="permissions")


class Role(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None

    permissions: List["RolePermission"] = Relationship(back_populates="role")
    users: List["UserRoleLink"] = Relationship(back_populates="role")


class UserRoleLink(SQLModel, table=True):
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", primary_key=True)
    role_id: Optional[int] = Field(default=None, foreign_key="role.id", primary_key=True)

    user: "User" = Relationship(back_populates="roles")
    role: Role = Relationship(back_populates="users")


class Member(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None
    api_key: Optional[str] = Field(default=None, index=True)
    security_server_ip: Optional[str] = Field(default=None, index=True)

    users: List["User"] = Relationship(back_populates="member")
    files: List["FileAsset"] = Relationship(back_populates="member")


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    full_name: Optional[str] = None
    hashed_password: str
    is_active: bool = True
    member_id: Optional[int] = Field(default=None, foreign_key="member.id")

    member: Optional["Member"] = Relationship(back_populates="users")
    roles: List["UserRoleLink"] = Relationship(back_populates="user")
    owned_files: List["FileAsset"] = Relationship(back_populates="owner")


class FileAsset(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str = Field(index=True)
    original_filename: str
    path: str
    size: int
    checksum: Optional[str] = Field(default=None, index=True)
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    owner_id: int = Field(foreign_key="user.id")
    member_id: int = Field(foreign_key="member.id")

    owner: User = Relationship(back_populates="owned_files")
    member: Member = Relationship(back_populates="files")
    shares: List["FileShare"] = Relationship(back_populates="file")


class FileShare(SQLModel, table=True):
    file_id: Optional[int] = Field(default=None, foreign_key="fileasset.id", primary_key=True)
    member_id: Optional[int] = Field(default=None, foreign_key="member.id", primary_key=True)
    granted_by_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    file: FileAsset = Relationship(back_populates="shares")
    member: Member = Relationship()


class AuditLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    actor_id: Optional[int] = Field(default=None, foreign_key="user.id")
    action: str = Field(index=True)
    target_type: str = Field(index=True)
    target_id: Optional[int] = Field(default=None, index=True)
    details: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
