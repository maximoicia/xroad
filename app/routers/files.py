from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from .. import crud, models
from ..deps import get_current_active_user, get_db
from ..schemas import FileRead, FileShareCreate
from ..security import Permission
from ..storage.file_service import FileService

router = APIRouter(prefix="/files", tags=["files"])
file_service = FileService()


@router.get("/", response_model=List[FileRead])
async def list_files(
    session: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
) -> List[models.FileAsset]:
    if not current_user.member_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not associated to a member")
    files = crud.file.get_files_for_member(session, current_user.member_id)
    return list(files)


@router.post("/", response_model=FileRead, status_code=status.HTTP_201_CREATED)
async def upload_file(
    uploaded_file: UploadFile = File(...),
    session: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
) -> models.FileAsset:
    if not current_user.member_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not associated to a member")

    if not uploaded_file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is required")

    uploaded_file.file.seek(0)
    saved_path = file_service.save(uploaded_file.file, uploaded_file.filename)
    size = saved_path.stat().st_size

    file_record = crud.file.create_file(
        session,
        file_path=saved_path,
        owner_id=current_user.id,
        member_id=current_user.member_id,
        original_filename=uploaded_file.filename,
        size=size,
    )

    crud.audit.create_log(
        session,
        actor_id=current_user.id,
        action="file.uploaded",
        target_type="file",
        target_id=file_record.id,
        details=f"Uploaded file {uploaded_file.filename}",
    )
    return file_record


@router.get("/{file_id}")
async def download_file(
    file_id: int,
    session: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
) -> StreamingResponse:
    file_record = crud.file.get_file(session, file_id)
    if not file_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    if not _user_can_access_file(session, current_user, file_record):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    file_handle = file_service.open(file_record.path)
    return StreamingResponse(
        file_handle,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={file_record.original_filename}"},
    )


@router.post("/{file_id}/share", response_model=FileRead)
async def share_file(
    file_id: int,
    share_in: FileShareCreate,
    session: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
) -> models.FileAsset:
    file_record = crud.file.get_file(session, file_id)
    if not file_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    if not _user_can_manage_file(session, current_user, file_record):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    for member_id in share_in.member_ids:
        if not crud.member.get_member(session, member_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Member {member_id} not found")

    updated_file = crud.file.share_file_with_members(
        session,
        file_record,
        member_ids=share_in.member_ids,
        granted_by=current_user.id,
    )

    crud.audit.create_log(
        session,
        actor_id=current_user.id,
        action="file.shared",
        target_type="file",
        target_id=file_id,
        details=f"Shared file {file_record.filename} with members {share_in.member_ids}",
    )
    return updated_file


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: int,
    session: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
) -> None:
    file_record = crud.file.get_file(session, file_id)
    if not file_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    if not _user_can_manage_file(session, current_user, file_record):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    file_service.remove(file_record.path)
    crud.file.delete_file(session, file_record)
    crud.audit.create_log(
        session,
        actor_id=current_user.id,
        action="file.deleted",
        target_type="file",
        target_id=file_id,
        details=f"Deleted file {file_record.filename}",
    )


def _user_can_access_file(session: Session, user: models.User, file: models.FileAsset) -> bool:
    if file.owner_id == user.id:
        return True
    if user.member_id == file.member_id:
        return True

    shared_members = {share.member_id for share in file.shares}
    return user.member_id in shared_members


def _user_can_manage_file(session: Session, user: models.User, file: models.FileAsset) -> bool:
    if file.owner_id == user.id:
        return True
    permissions = set(crud.user.get_user_permissions(session, user))
    return Permission.MANAGE_FILES in permissions
