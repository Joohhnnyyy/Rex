"""Capture dashboard screenshots and mascot clips for the launch video.

The dashboard's API calls (localhost:8000) are redirected to a demo API on :8010 that serves the seeded demo data in
demo-data/, so no private memory, files or finds end up in the video. Run: uv run python launches/rex-launch/capture.py
"""

import asyncio
import shutil
import sys
import subprocess
from pathlib import Path

from playwright.async_api import async_playwright

HERE = Path(__file__).parent
ASSETS = HERE / "assets"
W, H = 1600, 1000
REAL, DEMO = "http://localhost:8000", "http://localhost:8010"


async def demo_api(route):
    await route.continue_(url=route.request.url.replace(REAL, DEMO))


async def open_view(page, button: str | None):
    await page.goto("http://localhost:3000", wait_until="networkidle")
    if button:
        await page.get_by_role("button", name=button).first.click()
    await page.wait_for_timeout(2200)  # entrance animations and count-ups settle


async def shots(browser):
    ctx = await browser.new_context(viewport={"width": W, "height": H}, device_scale_factor=1.5)
    page = await ctx.new_page()
    await page.route(f"{REAL}/**", demo_api)
    for name, button in (
        ("overview", None),
        ("discover", "Discover"),
        ("files", "Files"),
        ("memory", "Memory"),
        ("agents", "Agents"),
    ):
        await open_view(page, button)
        await page.screenshot(path=str(ASSETS / f"ui-{name}.png"))
        print("shot", name)
    await open_view(page, None)
    await page.get_by_role("button", name="Immersive view").click()
    await page.wait_for_timeout(1800)
    await page.screenshot(path=str(ASSETS / "ui-immersive.png"))
    print("shot immersive")
    await ctx.close()


async def mascot_clips(browser):
    """A few seconds of each mascot state from the Lab tab, cropped to the mascot and its HUD."""
    tmp = HERE / "work" / "clips"
    tmp.mkdir(parents=True, exist_ok=True)
    for state in ("idle", "confused", "success", "surprised", "happy"):
        ctx = await browser.new_context(viewport={"width": W, "height": H}, record_video_dir=str(tmp),
                                        record_video_size={"width": W, "height": H})
        page = await ctx.new_page()
        await page.route(f"{REAL}/**", demo_api)
        await page.goto("http://localhost:3000", wait_until="networkidle")
        await page.keyboard.press("Meta+k")
        await page.keyboard.type("Go to Lab")
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(800)
        group = page.get_by_role("group", name="Preview a mascot state")
        await group.get_by_role("button").filter(has_text=state).first.click()
        box = await page.locator("[data-state]").first.bounding_box()
        await page.wait_for_timeout(4200)
        video = page.video
        await ctx.close()
        raw = Path(await video.path())
        x, y, s = int(box["x"]), int(box["y"]), int(min(box["width"], box["height"]))
        out = ASSETS / f"mascot-{state}.mp4"
        # skip the first 1.6 s (page load + click), crop the square stage, upscale for a crisp full-frame shot
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", "1.6", "-i", str(raw), "-t", "3.2",
                        "-vf", f"crop={s}:{s}:{x}:{y},scale=1080:1080:flags=lanczos,fps=30",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-g", "15", str(out)], check=True)
        raw.unlink()
        print("clip", state, box)
    shutil.rmtree(tmp, ignore_errors=True)


async def main():
    ASSETS.mkdir(exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        if "--clips-only" not in sys.argv:
            await shots(browser)
        await mascot_clips(browser)
        await browser.close()


asyncio.run(main())
