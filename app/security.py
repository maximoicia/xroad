from datetime import datetime, timedelta
from typing import Iterable, Optional

from jose import jwt
from passlib.context import CryptContext

from .config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()


class Permission:
    MANAGE_USERS = "manage:users"
    MANAGE_ROLES = "manage:roles"
    MANAGE_MEMBERS = "manage:members"
    MANAGE_SETTINGS = "manage:settings"
    MANAGE_FILES = "manage:files"
    VIEW_AUDIT_LOGS = "view:audit_logs"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    payload = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def has_permission(user_permissions: Iterable[str], required: str) -> bool:
    return required in set(user_permissions)
