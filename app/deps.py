from __future__ import annotations

from typing import Callable, Iterable, List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session

from . import crud, models
from .config import get_settings
from .database import get_session
from .schemas import TokenPayload

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


async def get_db() -> Iterable[Session]:
    with get_session() as session:
        yield session


async def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_db)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        token_data = TokenPayload(**payload)
    except JWTError as exc:
        raise credentials_exception from exc

    user = crud.user.get_user_by_username(session, token_data.sub)
    if not user:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: models.User = Depends(get_current_user)) -> models.User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user


def require_permissions(*permissions: str) -> Callable:
    async def dependency(
        current_user: models.User = Depends(get_current_active_user),
        session: Session = Depends(get_db),
    ) -> models.User:
        user_permissions: List[str] = crud.user.get_user_permissions(session, current_user)
        missing = [perm for perm in permissions if perm not in user_permissions]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"missing_permissions": missing},
            )
        return current_user

    return dependency
