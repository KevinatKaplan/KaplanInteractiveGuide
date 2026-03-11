from __future__ import annotations

import contextlib
import os
import subprocess
import sys
import time
import urllib.request
import zlib
from pathlib import Path

from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SERVER_URL = "http://127.0.0.1:8000"


def start_server() -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8000"],
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def wait_for_server(url: str, timeout: float = 20.0) -> None:
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=1) as resp:
                if resp.status == 200:
                    return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("Server did not start in time")


def make_solid_png(width: int, height: int, rgb: tuple[int, int, int]) -> bytes:
    r, g, b = rgb
    row = bytes([0]) + bytes([r, g, b]) * width
    raw = row * height
    compressed = zlib.compress(raw, level=6)

    def chunk(tag: bytes, data: bytes) -> bytes:
        length = len(data).to_bytes(4, "big")
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return length + tag + data + crc.to_bytes(4, "big")

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(
        b"IHDR",
        width.to_bytes(4, "big")
        + height.to_bytes(4, "big")
        + bytes([8, 2, 0, 0, 0]),
    )
    idat = chunk(b"IDAT", compressed)
    iend = chunk(b"IEND", b"")
    return signature + ihdr + idat + iend


def write_temp_image(tmp_dir: Path) -> Path:
    tmp_dir.mkdir(parents=True, exist_ok=True)
    img_path = tmp_dir / "playwright-test.png"
    img_path.write_bytes(make_solid_png(640, 360, (210, 210, 210)))
    return img_path


def create_demo_with_first_hotspot(page, img_path: Path) -> None:
    page.goto(f"{SERVER_URL}/builder", wait_until="domcontentloaded")
    page.fill("#start-title", "Playwright Demo")
    page.click("#create-demo")
    page.click("#add-step")
    page.set_input_files("#screen-upload", str(img_path))
    page.wait_for_selector("#screen-image:not(.hidden)")
    page.wait_for_selector("#image-stage:not(.hidden)")

    image_box = page.locator("#screen-image").bounding_box()
    if not image_box:
        raise RuntimeError("Image not visible for hotspot creation")

    start_x = image_box["x"] + image_box["width"] * 0.25
    start_y = image_box["y"] + image_box["height"] * 0.3
    end_x = image_box["x"] + image_box["width"] * 0.6
    end_y = image_box["y"] + image_box["height"] * 0.55

    page.mouse.move(start_x, start_y)
    page.mouse.down()
    page.mouse.move(end_x, end_y)
    page.mouse.up()

    page.wait_for_function(
        "document.getElementById('hotspot-readout').textContent.includes('Hotspot:')"
    )
    page.fill("#step-title", "Step One")
    page.click("#save-demo")


def test_hotspot_preview(page) -> None:
    with page.expect_popup() as popup_info:
        page.click("#preview-demo")
    preview = popup_info.value
    preview.wait_for_load_state("domcontentloaded")

    preview.wait_for_selector("#player-hotspot", state="visible")
    preview.wait_for_function(
        """
        () => {
          const el = document.getElementById('player-hotspot');
          if (!el) return false;
          const rect = el.getBoundingClientRect();
          return rect.width > 10 && rect.height > 10;
        }
        """
    )
    preview.close()


def test_click_advances_step(page) -> None:
    page.click("#add-hotspot")
    page.fill("#step-title", "Step Two")

    image_box = page.locator("#screen-image").bounding_box()
    if not image_box:
        raise RuntimeError("Image not visible for step two hotspot")

    start_x = image_box["x"] + image_box["width"] * 0.15
    start_y = image_box["y"] + image_box["height"] * 0.15
    end_x = image_box["x"] + image_box["width"] * 0.4
    end_y = image_box["y"] + image_box["height"] * 0.35

    page.mouse.move(start_x, start_y)
    page.mouse.down()
    page.mouse.move(end_x, end_y)
    page.mouse.up()

    page.wait_for_function(
        "document.getElementById('hotspot-readout').textContent.includes('Hotspot:')"
    )
    page.click("#save-demo")

    with page.expect_popup() as popup_info:
        page.click("#preview-demo")
    preview = popup_info.value
    preview.wait_for_load_state("domcontentloaded")

    preview.wait_for_function(
        "() => document.getElementById('tooltip-title')?.textContent.includes('Step One')"
    )

    hotspot = preview.locator("#player-hotspot").bounding_box()
    if not hotspot:
        raise RuntimeError("Preview hotspot missing for step one")

    click_x = hotspot["x"] + hotspot["width"] * 0.5
    click_y = hotspot["y"] + hotspot["height"] * 0.5
    preview.mouse.click(click_x, click_y)

    preview.wait_for_function(
        "() => document.getElementById('tooltip-title')?.textContent.includes('Step Two')"
    )
    preview.wait_for_function(
        "() => document.getElementById('progress')?.textContent.trim() === '2 / 2'"
    )
    preview.close()


def main() -> None:
    server = start_server()
    try:
        wait_for_server(SERVER_URL, timeout=25)

        tmp_dir = PROJECT_ROOT / "tests" / "tmp"
        img_path = write_temp_image(tmp_dir)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(viewport={"width": 1280, "height": 720})
            page = context.new_page()

            create_demo_with_first_hotspot(page, img_path)
            test_hotspot_preview(page)
            test_click_advances_step(page)

            context.close()
            browser.close()
    finally:
        with contextlib.suppress(Exception):
            server.terminate()
        with contextlib.suppress(Exception):
            server.wait(timeout=5)


if __name__ == "__main__":
    main()
