from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from .. import crud, models
from ..config import get_settings
from ..deps import get_current_active_user, get_db
from ..schemas import Token, UserRead
from ..security import create_access_token, verify_password

settings = get_settings()

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_db),
) -> Token:
    user = crud.user.get_user_by_username(session, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(subject=user.username, expires_delta=access_token_expires)
    return Token(access_token=access_token)


@router.get("/me", response_model=UserRead)
async def read_users_me(current_user: models.User = Depends(get_current_active_user)) -> models.User:
    return current_user
