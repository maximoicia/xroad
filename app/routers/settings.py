from fastapi import APIRouter, Depends

from .. import models
from ..config import get_settings
from ..deps import require_permissions
from ..schemas import SettingsRead
from ..security import Permission

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/", response_model=SettingsRead)
async def read_settings(_: models.User = Depends(require_permissions(Permission.MANAGE_SETTINGS))) -> SettingsRead:
    settings = get_settings()
    return SettingsRead(
        app_name=settings.app_name,
        access_token_expire_minutes=settings.access_token_expire_minutes,
        upload_dir=str(settings.upload_dir),
        cors_origins=settings.cors_origins,
    )
