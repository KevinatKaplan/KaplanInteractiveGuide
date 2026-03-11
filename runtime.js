from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError

from .. import db
from ..models import Demo
from .interface import DemoStore


class SqliteDemoStore(DemoStore):
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def init(self) -> None:
        db.init_db(self.db_path)

    def create(self, demo: Demo) -> None:
        db.insert_demo(demo.model_dump(), self.db_path)

    def update(self, demo: Demo) -> None:
        db.update_demo(demo.model_dump(), self.db_path)

    def get_by_id(self, demo_id: str) -> Demo | None:
        payload = db.fetch_demo_by_id(demo_id, self.db_path)
        if not payload:
            return None
        return Demo.model_validate(payload)

    def get_by_slug(self, slug: str) -> Demo | None:
        payload = db.fetch_demo_by_slug(slug, self.db_path)
        if not payload:
            return None
        return Demo.model_validate(payload)

    def slug_exists(self, slug: str) -> bool:
        return self.get_by_slug(slug) is not None

    def list_demos(self) -> list[Demo]:
        payloads = db.fetch_all_demos(self.db_path)
        demos: list[Demo] = []
        for payload in payloads:
            try:
                demos.append(Demo.model_validate(payload))
            except ValidationError:
                normalized = self._normalize_legacy_payload(payload)
                try:
                    demos.append(Demo.model_validate(normalized))
                except ValidationError:
                    demos.append(
                        Demo(
                            id=normalized.get("id", "legacy-demo"),
                            slug=normalized.get("slug", "legacy-demo"),
                            title=normalized.get("title", "Legacy Demo"),
                            status=normalized.get("status", "draft"),
                            tags=normalized.get("tags", []),
                            startStepId=None,
                            screens=[],
                            steps=[],
                            chapters=[],
                            ui=normalized.get("ui", {"badge": {}, "intro": {}}),
                            createdAt=normalized.get("createdAt", "1970-01-01T00:00:00+00:00"),
                            updatedAt=normalized.get("updatedAt", "1970-01-01T00:00:00+00:00"),
                        )
                    )
        return demos

    def delete(self, demo_id: str) -> bool:
        return db.delete_demo(demo_id, self.db_path)

    def _normalize_legacy_payload(self, payload: dict) -> dict:
        normalized = dict(payload)
        normalized["schemaVersion"] = int(normalized.get("schemaVersion") or 1)
        normalized["status"] = normalized.get("status") or "draft"
        normalized["tags"] = [str(tag).strip() for tag in (normalized.get("tags") or []) if str(tag).strip()]
        normalized["ui"] = dict(normalized.get("ui") or {})
        normalized["ui"]["badge"] = dict(normalized["ui"].get("badge") or {})
        normalized["ui"]["intro"] = dict(normalized["ui"].get("intro") or {})
        normalized["ui"]["intro"]["enabled"] = bool(normalized["ui"]["intro"].get("enabled", True))
        normalized["ui"]["intro"]["title"] = str(normalized["ui"]["intro"].get("title") or "")
        normalized["ui"]["intro"]["body"] = str(normalized["ui"]["intro"].get("body") or "")
        normalized["ui"]["intro"]["startLabel"] = str(
            normalized["ui"]["intro"].get("startLabel") or "Start Interactive Demo"
        )
        normalized["ui"]["intro"]["skipLabel"] = str(normalized["ui"]["intro"].get("skipLabel") or "Skip Intro")
        normalized["chapters"] = list(normalized.get("chapters") or [])
        normalized["screens"] = list(normalized.get("screens") or [])
        normalized["steps"] = list(normalized.get("steps") or [])

        for index, screen in enumerate(normalized["screens"]):
            media_url = screen.get("mediaUrl") or screen.get("imageUrl") or ""
            media_type = screen.get("mediaType") or "image"
            if media_type not in {"image", "video", "html"}:
                media_type = "image"
            screen["mediaType"] = media_type
            screen["mediaUrl"] = media_url
            screen["imageUrl"] = screen.get("imageUrl") or media_url
            screen["fitMode"] = screen.get("fitMode") or "contain"
            screen["interactionMode"] = screen.get("interactionMode") or "guided"
            screen["order"] = int(screen.get("order", index))

        for index, step in enumerate(normalized["steps"]):
            step["title"] = step.get("title") or "Step"
            step["body"] = step.get("body") or ""
            hotspot_type = step.get("hotspotType") or "click"
            if hotspot_type not in {"click", "highlight", "none"}:
                hotspot_type = "click"
            step["hotspotType"] = hotspot_type
            hint_type = step.get("hintType") or "click"
            if hint_type not in {"click", "arrow", "none"}:
                hint_type = "click"
            step["hintType"] = hint_type
            tooltip_position = step.get("tooltipPosition") or "auto"
            if tooltip_position not in {"auto", "top", "right", "bottom", "left"}:
                tooltip_position = "auto"
            step["tooltipPosition"] = tooltip_position
            step["autoPlay"] = bool(step.get("autoPlay", False))
            step["advanceOnTooltipClick"] = bool(step.get("advanceOnTooltipClick", False))
            step["order"] = int(step.get("order", index))
            hotspot = step.get("hotspot")
            if hotspot:
                for key in ("xPct", "yPct", "wPct", "hPct"):
                    value = hotspot.get(key, 0)
                    if value > 1:
                        hotspot[key] = value / 100.0

        return normalized
