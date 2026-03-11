from __future__ import annotations

import base64
import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_MODE", "local")
    monkeypatch.setenv("DEMO_DB_PATH", str(tmp_path / "app.db"))
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://localhost,http://127.0.0.1")
    monkeypatch.setenv("MAX_UPLOAD_BYTES", str(25 * 1024 * 1024))

    import app.main as app_main

    module = importlib.reload(app_main)
    with TestClient(module.app) as test_client:
        yield test_client


def create_demo(client: TestClient, title: str = "API Test Demo") -> dict:
    response = client.post("/api/demos", json={"title": title})
    assert response.status_code == 200
    return response.json()


def valid_payload(demo: dict) -> dict:
    return {
        "id": demo["id"],
        "slug": demo["slug"],
        "title": "Updated Demo",
        "schemaVersion": 1,
        "status": "draft",
        "startStepId": "step-1",
        "chapters": [{"id": "chapter-1", "title": "Intro", "order": 0}],
        "screens": [
            {
                "id": "screen-1",
                "mediaType": "image",
                "mediaUrl": "/uploads/example.png",
                "imageUrl": "/uploads/example.png",
                "naturalWidth": 1280,
                "naturalHeight": 720,
                "duration": None,
                "order": 0,
            }
        ],
        "steps": [
            {
                "id": "step-1",
                "screenId": "screen-1",
                "title": "Step 1",
                "body": "Click here",
                "hotspot": {"xPct": 0.2, "yPct": 0.2, "wPct": 0.3, "hPct": 0.2},
                "hotspotType": "highlight",
                "hintType": "arrow",
                "tooltipPosition": "left",
                "timeSec": None,
                "chapterId": "chapter-1",
                "nextStepId": None,
                "order": 0,
            }
        ],
        "createdAt": demo["createdAt"],
        "updatedAt": demo["updatedAt"],
    }


def test_create_demo_defaults(client: TestClient) -> None:
    demo = create_demo(client)
    assert demo["status"] == "draft"
    assert demo["schemaVersion"] == 1
    assert demo["screens"] == []
    assert demo["steps"] == []


def test_platform_sample_demo_is_seeded(client: TestClient) -> None:
    response = client.get("/api/demos/platform-sample")
    assert response.status_code == 200
    payload = response.json()
    assert payload["slug"] == "platform-sample"
    assert payload["status"] == "published"
    assert len(payload["screens"]) >= 4
    assert len(payload["steps"]) >= 6


def test_status_persists(client: TestClient) -> None:
    demo = create_demo(client)
    payload = valid_payload(demo)
    payload["status"] = "published"
    response = client.put(f"/api/demos/{demo['id']}", json=payload)
    assert response.status_code == 200
    saved = response.json()
    assert saved["status"] == "published"


def test_rejects_invalid_hotspot_and_missing_screen_reference(client: TestClient) -> None:
    demo = create_demo(client)
    payload = valid_payload(demo)
    payload["steps"][0]["screenId"] = "missing-screen"
    payload["steps"][0]["hotspot"]["xPct"] = 1.2
    response = client.put(f"/api/demos/{demo['id']}", json=payload)
    assert response.status_code == 422
    details = response.json()["detail"]
    combined = " ".join(item["msg"] for item in details if isinstance(item, dict))
    assert "screenId" in combined or "hotspot" in combined


def test_import_export_round_trip(client: TestClient) -> None:
    demo = create_demo(client)
    payload = valid_payload(demo)
    save_response = client.put(f"/api/demos/{demo['id']}", json=payload)
    assert save_response.status_code == 200

    export_response = client.get(f"/api/demos/{demo['id']}/export")
    assert export_response.status_code == 200
    exported = export_response.json()
    assert exported["id"] == demo["id"]
    assert exported["steps"][0]["title"] == "Step 1"

    import_response = client.post("/api/demos/import", json=exported)
    assert import_response.status_code == 200
    imported = import_response.json()
    assert imported["id"] != demo["id"]
    assert imported["steps"][0]["title"] == "Step 1"
    assert imported["chapters"][0]["title"] == "Intro"


def test_demo_config_endpoint_shape(client: TestClient) -> None:
    demo = create_demo(client)
    payload = valid_payload(demo)
    payload["screens"][0]["mediaType"] = "html"
    payload["screens"][0]["mediaUrl"] = "https://example.com"
    payload["screens"][0]["markers"] = [1.2, 2.5, 2.5]
    payload["screens"][0]["fitMode"] = "contain"
    payload["screens"][0]["interactionMode"] = "guided"
    payload["steps"][0]["hotspotId"] = "hotspot-1"
    payload["steps"][0]["autoPlay"] = False
    payload["steps"][0]["advanceOnTooltipClick"] = False

    save_response = client.put(f"/api/demos/{demo['id']}", json=payload)
    assert save_response.status_code == 200

    config_response = client.get(f"/api/demos/{demo['slug']}")
    assert config_response.status_code == 200
    config = config_response.json()
    assert config["id"] == demo["id"]
    assert config["slug"] == demo["slug"]
    assert config["screens"][0]["mediaType"] == "html"
    assert config["screens"][0]["markers"] == [1.2, 2.5]
    assert config["steps"][0]["hotspotId"] == "hotspot-1"


def test_upload_rejects_non_media_content(client: TestClient) -> None:
    response = client.post(
        "/api/uploads",
        files={"file": ("note.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 400


def test_upload_accepts_image(client: TestClient) -> None:
    png_bytes = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO2NfcoAAAAASUVORK5CYII="
    )
    response = client.post(
        "/api/uploads",
        files={"file": ("pixel.png", png_bytes, "image/png")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["mediaType"] == "image"
    assert payload["mediaUrl"].startswith("/uploads/")
    assert payload["imageUrl"] == payload["mediaUrl"]


def test_embed_js_contains_event_bridge(client: TestClient) -> None:
    response = client.get("/embed.js?slug=demo-slug")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/javascript")
    body = response.text
    assert "data-demo-slug" in body
    assert "supaclone:start" in body
    assert "supaclone:step" in body
    assert "supaclone:complete" in body


def test_showcase_api_filters_by_tag(client: TestClient) -> None:
    demo = create_demo(client, title="Tagged Demo")
    payload = valid_payload(demo)
    payload["tags"] = ["sales", "onboarding"]
    save_response = client.put(f"/api/demos/{demo['id']}", json=payload)
    assert save_response.status_code == 200

    all_response = client.get("/api/showcases/all")
    assert all_response.status_code == 200
    all_payload = all_response.json()
    assert any(item["id"] == demo["id"] for item in all_payload["demos"])
    assert "sales" in all_payload["tags"]

    filtered_response = client.get("/api/showcases/all?tag=sales")
    assert filtered_response.status_code == 200
    filtered = filtered_response.json()["demos"]
    assert len(filtered) >= 1
    assert all("sales" in item["tags"] for item in filtered)


def test_analytics_event_ingest_and_summary(client: TestClient) -> None:
    demo = create_demo(client, title="Analytics Demo")
    payload = valid_payload(demo)
    payload["steps"] = [
        {
            "id": "step-1",
            "screenId": "screen-1",
            "title": "Step 1",
            "body": "First step",
            "hotspot": {"xPct": 0.2, "yPct": 0.2, "wPct": 0.2, "hPct": 0.2},
            "hotspotType": "click",
            "hintType": "click",
            "tooltipPosition": "auto",
            "timeSec": None,
            "chapterId": "chapter-1",
            "nextStepId": "step-2",
            "order": 0,
        },
        {
            "id": "step-2",
            "screenId": "screen-1",
            "title": "Step 2",
            "body": "Second step",
            "hotspot": {"xPct": 0.5, "yPct": 0.5, "wPct": 0.2, "hPct": 0.2},
            "hotspotType": "highlight",
            "hintType": "arrow",
            "tooltipPosition": "right",
            "timeSec": None,
            "chapterId": "chapter-1",
            "nextStepId": None,
            "order": 1,
        },
    ]
    payload["startStepId"] = "step-1"
    save_response = client.put(f"/api/demos/{demo['id']}", json=payload)
    assert save_response.status_code == 200

    events = [
        {"eventName": "supaclone:demo_view", "sessionId": "sess-a"},
        {"eventName": "supaclone:demo_start", "sessionId": "sess-a"},
        {"eventName": "supaclone:step_view", "sessionId": "sess-a", "stepId": "step-1", "index": 0},
        {"eventName": "supaclone:step_complete", "sessionId": "sess-a", "stepId": "step-1", "index": 0},
        {"eventName": "supaclone:step_view", "sessionId": "sess-a", "stepId": "step-2", "index": 1},
        {"eventName": "supaclone:step_complete", "sessionId": "sess-a", "stepId": "step-2", "index": 1},
        {"eventName": "supaclone:demo_complete", "sessionId": "sess-a"},
        {"eventName": "supaclone:demo_view", "sessionId": "sess-b"},
        {"eventName": "supaclone:demo_start", "sessionId": "sess-b"},
        {"eventName": "supaclone:step_view", "sessionId": "sess-b", "stepId": "step-1", "index": 0},
    ]
    for event in events:
        response = client.post(
            "/api/analytics/events",
            json={"demoId": demo["id"], "slug": demo["slug"], **event},
        )
        assert response.status_code == 200

    summary_response = client.get(f"/api/analytics/{demo['slug']}/summary")
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["views"] == 2
    assert summary["starts"] == 2
    assert summary["completes"] == 1
    assert summary["completionRate"] == 50.0
    assert summary["eventTotals"]["supaclone:step_view"] == 3
    assert summary["stepDropoff"][0]["title"] == "Step 1"
    assert summary["stepDropoff"][0]["dropoff"] == 1


def test_analytics_rejects_step_event_without_step_id(client: TestClient) -> None:
    demo = create_demo(client, title="Analytics Validation Demo")
    payload = valid_payload(demo)
    save_response = client.put(f"/api/demos/{demo['id']}", json=payload)
    assert save_response.status_code == 200

    response = client.post(
        "/api/analytics/events",
        json={
            "eventName": "supaclone:step_view",
            "demoId": demo["id"],
            "slug": demo["slug"],
            "sessionId": "sess-validation",
        },
    )
    assert response.status_code == 422
    assert "stepId is required" in response.text


def test_analytics_event_uses_cookie_fallback_session(client: TestClient) -> None:
    demo = create_demo(client, title="Cookie Session Demo")

    response = client.post(
        "/api/analytics/events",
        json={
            "eventName": "supaclone:demo_view",
            "demoId": demo["id"],
            "slug": demo["slug"],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["sessionId"]
    assert response.cookies.get("supaclone_session_id") == payload["sessionId"]


def test_analytics_csv_export_contains_metrics(client: TestClient) -> None:
    demo = create_demo(client, title="CSV Demo")
    payload = valid_payload(demo)
    save_response = client.put(f"/api/demos/{demo['id']}", json=payload)
    assert save_response.status_code == 200

    response = client.post(
        "/api/analytics/events",
        json={
            "eventName": "supaclone:demo_view",
            "demoId": demo["id"],
            "slug": demo["slug"],
            "sessionId": "sess-csv",
        },
    )
    assert response.status_code == 200

    csv_response = client.get(f"/api/analytics/{demo['slug']}/events.csv")
    assert csv_response.status_code == 200
    assert csv_response.headers["content-type"].startswith("text/csv")
    body = csv_response.text
    assert "metric,value" in body
    assert "completion_rate_pct" in body
    assert "Step 1" in body


def test_auto_build_without_key_uses_fallback_with_varied_hotspots(client: TestClient) -> None:
    demo = create_demo(client, title="Auto Build Fallback")
    payload = valid_payload(demo)
    payload["screens"][0]["mediaType"] = "video"
    payload["screens"][0]["mediaUrl"] = "/uploads/sample.webm"
    payload["screens"][0]["imageUrl"] = None
    payload["screens"][0]["duration"] = 24.0
    payload["steps"] = []
    payload["startStepId"] = None

    save_response = client.put(f"/api/demos/{demo['id']}", json=payload)
    assert save_response.status_code == 200

    frame_b64 = base64.b64encode(b"x" * 120).decode("ascii")
    auto_build_response = client.post(
        f"/api/demos/{demo['id']}/auto-build",
        json={
            "screenId": "screen-1",
            "overwrite": True,
            "frames": [
                {"timeSec": 1.2, "imageBase64": frame_b64},
                {"timeSec": 8.0, "imageBase64": frame_b64},
                {"timeSec": 16.5, "imageBase64": frame_b64},
                {"timeSec": 22.1, "imageBase64": frame_b64},
            ],
        },
    )
    assert auto_build_response.status_code == 200
    assert auto_build_response.headers.get("x-autobuild-mode") == "fallback"
    assert "OPENAI_API_KEY" in (auto_build_response.headers.get("x-autobuild-reason") or "")

    updated = auto_build_response.json()
    assert len(updated["steps"]) >= 3
    hotspots = {
        (
            round(step["hotspot"]["xPct"], 4),
            round(step["hotspot"]["yPct"], 4),
            round(step["hotspot"]["wPct"], 4),
            round(step["hotspot"]["hPct"], 4),
        )
        for step in updated["steps"]
    }
    assert len(hotspots) > 1
    assert all("Draft generated from frame" in step["body"] for step in updated["steps"])


def test_auto_build_from_codex_draft_applies_steps(client: TestClient) -> None:
    demo = create_demo(client, title="Codex Draft Import")
    payload = valid_payload(demo)
    save_response = client.put(f"/api/demos/{demo['id']}", json=payload)
    assert save_response.status_code == 200

    draft_response = client.post(
        f"/api/demos/{demo['id']}/auto-build/from-draft",
        json={
            "screenId": "screen-1",
            "overwrite": True,
            "chapters": [{"title": "Setup"}, {"title": "Validation"}],
            "steps": [
                {
                    "title": "Open Redirect Settings",
                    "body": "Open the redirects page from settings.",
                    "timeSec": 2.3,
                    "chapterTitle": "Setup",
                    "hintType": "click",
                    "tooltipPosition": "right",
                    "hotspot": {"xPct": 0.12, "yPct": 0.2, "wPct": 0.24, "hPct": 0.14},
                },
                {
                    "title": "Verify Redirect",
                    "body": "Check for the success notice.",
                    "timeSec": 8.1,
                    "chapterTitle": "Validation",
                    "hintType": "arrow",
                    "tooltipPosition": "auto",
                    "hotspot": {"xPct": 0.54, "yPct": 0.72, "wPct": 0.3, "hPct": 0.11},
                },
            ],
        },
    )
    assert draft_response.status_code == 200
    assert draft_response.headers.get("x-autobuild-mode") == "codex-draft"
    updated = draft_response.json()
    assert len(updated["steps"]) == 2
    assert updated["steps"][0]["title"] == "Open Redirect Settings"
    assert updated["steps"][1]["hintType"] == "arrow"
    assert len(updated["chapters"]) == 2


def test_feedback_event_is_aggregated_in_summary_and_csv(client: TestClient) -> None:
    demo = create_demo(client, title="Feedback Demo")
    payload = valid_payload(demo)
    save_response = client.put(f"/api/demos/{demo['id']}", json=payload)
    assert save_response.status_code == 200

    feedback_response = client.post(
        "/api/analytics/events",
        json={
            "eventName": "supaclone:feedback_submit",
            "demoId": demo["id"],
            "slug": demo["slug"],
            "sessionId": "sess-feedback",
            "feedbackScore": 4,
            "feedbackText": "Very clear demo, thanks.",
        },
    )
    assert feedback_response.status_code == 200

    summary_response = client.get(f"/api/analytics/{demo['slug']}/summary")
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["feedbackCount"] == 1
    assert summary["feedbackAverageScore"] == 4.0
    assert summary["feedbackComments"][0]["text"] == "Very clear demo, thanks."

    csv_response = client.get(f"/api/analytics/{demo['slug']}/events.csv")
    assert csv_response.status_code == 200
    body = csv_response.text
    assert "feedback_count,1" in body
    assert "feedback_avg_score,4.0" in body
    assert "Very clear demo, thanks." in body


def test_feedback_event_requires_score(client: TestClient) -> None:
    demo = create_demo(client, title="Feedback Validation")
    response = client.post(
        "/api/analytics/events",
        json={
            "eventName": "supaclone:feedback_submit",
            "demoId": demo["id"],
            "slug": demo["slug"],
            "sessionId": "sess-feedback-validation",
            "feedbackText": "Missing score should fail.",
        },
    )
    assert response.status_code == 422
    assert "feedbackScore is required" in response.text


def test_admin_requires_login(client: TestClient) -> None:
    response = client.get("/admin")
    assert response.status_code == 200
    assert "Admin Access" in response.text
    assert "Open Dashboard" in response.text


def test_admin_login_and_delete_demo(client: TestClient) -> None:
    demo = create_demo(client, title="Delete Me")

    unauthorized_delete = client.post(f"/admin/demos/{demo['id']}/delete")
    assert unauthorized_delete.status_code == 403

    login_response = client.post("/admin/login", data={"password": "kaplanlife"}, follow_redirects=False)
    assert login_response.status_code == 303
    assert login_response.headers["location"] == "/admin"
    assert "ig_admin_session" in login_response.cookies

    dashboard = client.get("/admin")
    assert dashboard.status_code == 200
    assert "Edit in Builder" in dashboard.text
    assert f"/builder?demo={demo['slug']}" in dashboard.text

    delete_response = client.post(f"/admin/demos/{demo['id']}/delete", follow_redirects=False)
    assert delete_response.status_code == 303
    assert delete_response.headers["location"] == "/admin"

    missing = client.get(f"/api/demos/{demo['slug']}")
    assert missing.status_code == 404
