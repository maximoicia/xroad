from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import crud
from .config import get_settings
from .database import get_session, init_db
from .routers import audit, auth, files, members, roles, settings as settings_router, users
from .security import Permission

settings = get_settings()
app = FastAPI(title=settings.app_name)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.cors_origins],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    bootstrap_defaults()


def bootstrap_defaults() -> None:
    default_roles = {
        "administrator": {
            "description": "Full access to all administrative features",
            "permissions": [
                Permission.MANAGE_USERS,
                Permission.MANAGE_ROLES,
                Permission.MANAGE_MEMBERS,
                Permission.MANAGE_SETTINGS,
                Permission.MANAGE_FILES,
                Permission.VIEW_AUDIT_LOGS,
            ],
        },
        "member": {
            "description": "Regular member user with file collaboration rights",
            "permissions": [],
        },
    }

    with get_session() as session:
        for role_name, role_data in default_roles.items():
            role = crud.role.get_role_by_name(session, role_name)
            if not role:
                role = crud.role.create_role(
                    session,
                    name=role_name,
                    description=role_data["description"],
                    permissions=role_data["permissions"],
                )
            else:
                crud.role.update_role(
                    session,
                    role,
                    description=role_data["description"],
                    permissions=role_data["permissions"],
                )

        admin_user = crud.user.get_user_by_username(session, settings.initial_admin_username)
        if not admin_user:
            admin_role = crud.role.get_role_by_name(session, "administrator")
            if admin_role is None:
                raise RuntimeError("Administrator role missing during bootstrap")
            crud.user.create_user(
                session,
                username=settings.initial_admin_username,
                email=settings.initial_admin_email,
                password=settings.initial_admin_password,
                full_name="System Administrator",
                member_id=None,
                role_ids=[admin_role.id],
            )


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(roles.router)
app.include_router(members.router)
app.include_router(files.router)
app.include_router(audit.router)
app.include_router(settings_router.router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
