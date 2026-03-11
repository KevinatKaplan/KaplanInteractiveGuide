from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from fastapi import FastAPI, UploadFile

from ..models import Demo


@dataclass(frozen=True)
class MediaUploadResult:
    media_type: str
    media_url: str
    image_url: str


class DemoStore(ABC):
    @abstractmethod
    def init(self) -> None:
        pass

    @abstractmethod
    def create(self, demo: Demo) -> None:
        pass

    @abstractmethod
    def update(self, demo: Demo) -> None:
        pass

    @abstractmethod
    def get_by_id(self, demo_id: str) -> Demo | None:
        pass

    @abstractmethod
    def get_by_slug(self, slug: str) -> Demo | None:
        pass

    @abstractmethod
    def slug_exists(self, slug: str) -> bool:
        pass

    @abstractmethod
    def list_demos(self) -> list[Demo]:
        pass

    @abstractmethod
    def delete(self, demo_id: str) -> bool:
        pass


class MediaStore(ABC):
    @abstractmethod
    def init(self) -> None:
        pass

    @abstractmethod
    def mount(self, app: FastAPI) -> None:
        pass

    @abstractmethod
    async def save_upload(self, file: UploadFile) -> MediaUploadResult:
        pass
