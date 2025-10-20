from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable, Sequence

from sqlmodel import Session, delete, select

from .. import models


def _calculate_checksum(path: Path) -> str:
    sha256 = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_file(session: Session, file_id: int) -> Optional[models.FileAsset]:
    return session.get(models.FileAsset, file_id)


def get_files_for_member(session: Session, member_id: int, *, include_shared: bool = True) -> Sequence[models.FileAsset]:
    statement = select(models.FileAsset).where(models.FileAsset.member_id == member_id)
    owned = session.exec(statement).all()
    if not include_shared:
        return owned

    shared_statement = (
        select(models.FileAsset)
        .join(models.FileShare)
        .where(models.FileShare.member_id == member_id)
    )
    shared = session.exec(shared_statement).all()
    return list({file.id: file for file in owned + shared}.values())


def create_file(session: Session, *, file_path: Path, owner_id: int, member_id: int,
                original_filename: str, size: int) -> models.FileAsset:
    checksum = _calculate_checksum(file_path)
    db_file = models.FileAsset(
        filename=file_path.name,
        original_filename=original_filename,
        path=str(file_path),
        size=size,
        checksum=checksum,
        owner_id=owner_id,
        member_id=member_id,
    )
    session.add(db_file)
    session.commit()
    session.refresh(db_file)
    return db_file


def share_file_with_members(session: Session, file: models.FileAsset, member_ids: Iterable[int], granted_by: int) -> models.FileAsset:
    session.exec(delete(models.FileShare).where(models.FileShare.file_id == file.id))
    session.flush()

    for member_id in member_ids:
        session.add(
            models.FileShare(
                file_id=file.id,
                member_id=member_id,
                granted_by_id=granted_by,
            )
        )

    session.commit()
    session.refresh(file)
    return file


def revoke_file_shares(session: Session, file: models.FileAsset) -> None:
    session.exec(delete(models.FileShare).where(models.FileShare.file_id == file.id))
    session.commit()


def delete_file(session: Session, file: models.FileAsset) -> None:
    session.exec(delete(models.FileShare).where(models.FileShare.file_id == file.id))
    session.delete(file)
    session.commit()
