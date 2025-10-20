from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import BinaryIO

from ..config import get_settings

settings = get_settings()


class FileService:
    """Utility class to manage file persistence on disk."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or settings.upload_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, source: BinaryIO, original_filename: str) -> Path:
        extension = Path(original_filename).suffix
        filename = f"{uuid.uuid4().hex}{extension}"
        destination = self.base_dir / filename
        with destination.open("wb") as out_file:
            shutil.copyfileobj(source, out_file)
        return destination

    def remove(self, path: str) -> None:
        file_path = Path(path)
        if file_path.exists():
            file_path.unlink()

    def open(self, path: str) -> BinaryIO:
        return open(path, "rb")
