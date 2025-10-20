from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import AnyHttpUrl, BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    exp: int


class PermissionRead(BaseModel):
    permission: str

    class Config:
        orm_mode = True


class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    permissions: List[str] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    description: Optional[str] = None
    permissions: Optional[List[str]] = None


class RoleRead(RoleBase):
    id: int
    permissions: List[PermissionRead] = Field(default_factory=list)

    class Config:
        orm_mode = True


class MemberBase(BaseModel):
    name: str
    description: Optional[str] = None
    api_key: Optional[str] = None
    security_server_ip: Optional[str] = Field(default=None, alias="securityServerIp")

    class Config:
        allow_population_by_field_name = True


class MemberCreate(MemberBase):
    pass


class MemberUpdate(BaseModel):
    description: Optional[str] = None
    api_key: Optional[str] = None
    security_server_ip: Optional[str] = Field(default=None, alias="securityServerIp")

    class Config:
        allow_population_by_field_name = True


class MemberRead(MemberBase):
    id: int

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(min_length=8)
    member_id: Optional[int] = None
    role_ids: List[int] = Field(default_factory=list)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(default=None, min_length=8)
    member_id: Optional[int] = None
    role_ids: Optional[List[int]] = None


class UserRead(UserBase):
    id: int
    member: Optional[MemberRead] = None
    roles: List[RoleRead] = Field(default_factory=list)

    class Config:
        orm_mode = True


class FileShareCreate(BaseModel):
    member_ids: List[int]


class FileShareRead(BaseModel):
    member_id: int
    member: Optional[MemberRead] = None
    granted_by_id: int
    created_at: datetime

    class Config:
        orm_mode = True


class FileRead(BaseModel):
    id: int
    filename: str
    original_filename: str
    size: int
    uploaded_at: datetime
    owner_id: int
    member_id: int
    checksum: Optional[str] = None
    shares: List[FileShareRead] = Field(default_factory=list)

    class Config:
        orm_mode = True


class AuditLogRead(BaseModel):
    id: int
    actor_id: Optional[int]
    action: str
    target_type: str
    target_id: Optional[int]
    details: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True


class SettingsRead(BaseModel):
    app_name: str
    access_token_expire_minutes: int
    upload_dir: str
    cors_origins: List[AnyHttpUrl] = Field(default_factory=list)
