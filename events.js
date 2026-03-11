from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles

from .interface import MediaStore, MediaUploadResult


class LocalMediaStore(MediaStore):
    _image_suffixes = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
    _video_suffixes = {".mp4", ".webm", ".mov", ".m4v"}

    def __init__(
        self,
        upload_dir: Path,
        public_prefix: str = "/uploads",
        max_upload_bytes: int = 25 * 1024 * 1024,
    ) -> None:
        self.upload_dir = upload_dir
        self.public_prefix = public_prefix
        self.max_upload_bytes = max_upload_bytes

    def init(self) -> None:
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def mount(self, app: FastAPI) -> None:
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        app.mount(self.public_prefix, StaticFiles(directory=self.upload_dir), name="uploads")

    async def save_upload(self, file: UploadFile) -> MediaUploadResult:
        content_type = (file.content_type or "").lower()
        if content_type.startswith("image/"):
            media_type = "image"
            allowed_suffixes = self._image_suffixes
            fallback_suffix = ".png"
        elif content_type.startswith("video/"):
            media_type = "video"
            allowed_suffixes = self._video_suffixes
            fallback_suffix = ".mp4"
        else:
            raise HTTPException(status_code=400, detail="Only image or video uploads are supported")

        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in allowed_suffixes:
            suffix = fallback_suffix

        contents = await file.read(self.max_upload_bytes + 1)
        if len(contents) > self.max_upload_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File is too large. Limit is {self.max_upload_bytes} bytes.",
            )

        filename = f"{uuid.uuid4().hex}{suffix}"
        target = self.upload_dir / filename
        target.write_bytes(contents)

        media_url = f"{self.public_prefix}/{filename}"
        return MediaUploadResult(
            media_type=media_type,
            media_url=media_url,
            image_url=media_url,
        )
