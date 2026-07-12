#!/usr/bin/env python3
"""Capture full-color README screenshots from the Typatro TUI.

Run from repo root::

    python scripts/capture_readme_screenshots.py

Requires ``rsvg-convert`` on PATH (librsvg) to convert SVG exports to PNG.

Headless Textual honors the ``NO_COLOR`` environment variable. When it is set,
the app applies a monochrome filter and exported SVGs lose theme colors. This
script unsets ``NO_COLOR`` and sets truecolor terminal variables before capture.
"""

from __future__ import annotations

import asyncio
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_IMAGES = REPO_ROOT / "docs" / "images"
SCREEN_SIZE = (148, 51)
PNG_WIDTH = 1482

THEME_COLORS = {
    "#eac058",
    "#0093ff",
    "#fe5f55",
    "#1e2b3c",
    "#8a9bb5",
    "#f4f4f4",
}


def _ensure_capture_env() -> None:
    os.environ.pop("NO_COLOR", None)
    os.environ["TERM"] = "xterm-256color"
    os.environ["COLORTERM"] = "truecolor"


def _svg_color_report(svg: str) -> tuple[int, set[str]]:
    colors = {match.group(1).lower() for match in re.finditer(r"fill: (#[0-9a-fA-F]{6})", svg)}
    return len(colors), THEME_COLORS & colors


def _svg_to_png(svg_path: Path, png_path: Path) -> None:
    subprocess.run(
        [
            "rsvg-convert",
            "-w",
            str(PNG_WIDTH),
            "-f",
            "png",
            "-o",
            str(png_path),
            str(svg_path),
        ],
        check=True,
    )


def _write_screenshot(app, stem: str) -> None:
    svg = app.export_screenshot()
    color_count, theme_hits = _svg_color_report(svg)
    if not theme_hits:
        raise RuntimeError(
            f"{stem}: screenshot has no balatro theme colors "
            f"({color_count} fill colors total). Is NO_COLOR set?"
        )

    svg_path = DOCS_IMAGES / f"{stem}.svg"
    png_path = DOCS_IMAGES / f"{stem}.png"
    svg_path.write_text(svg, encoding="utf-8")
    _svg_to_png(svg_path, png_path)
    print(f"wrote {png_path.name} ({color_count} colors, theme: {sorted(theme_hits)})")


async def _capture_run_mode(stem: str) -> None:
    from typatro.src import config_parser
    from typatro.ui.tui import Typatro
    from typatro.ui.widgets import Space
    from typatro.ui.widgets.balatro import ScorePanel

    config_parser.set("theme", "balatro")
    config_parser.set("game_mode", "run")
    app = Typatro()
    async with app.run_test(size=SCREEN_SIZE) as pilot:
        await pilot.pause(0.6)
        space = app.screen.query_one(Space)
        panel = app.screen.query_one(ScorePanel)
        text = space.paragraph.plain
        for _ in range(min(80, len(text))):
            if space.tracker.cursor_pos >= len(text):
                break
            space.keypress(text[space.tracker.cursor_pos])
        await pilot.pause(0.3)
        panel.refresh()
        await pilot.pause(0.3)
        _write_screenshot(app, stem)


async def _capture_joker_pick() -> None:
    from typatro.src import config_parser
    from typatro.ui.screens.joker_choice import JokerChoiceScreen
    from typatro.ui.tui import Typatro

    config_parser.set("theme", "balatro")
    config_parser.set("game_mode", "run")
    app = Typatro()
    async with app.run_test(size=SCREEN_SIZE) as pilot:
        await pilot.pause(0.4)
        app.push_screen(JokerChoiceScreen())
        await pilot.pause(0.8)
        _write_screenshot(app, "joker-pick")


async def _capture_classic_mode() -> None:
    from typatro.src import config_parser
    from typatro.ui.tui import Typatro

    config_parser.set("theme", "balatro")
    config_parser.set("game_mode", "classic")
    app = Typatro()
    async with app.run_test(size=SCREEN_SIZE) as pilot:
        await pilot.pause(0.6)
        _write_screenshot(app, "classic-mode")
    config_parser.set("game_mode", "run")


async def main() -> None:
    if shutil_which("rsvg-convert") is None:
        print("error: rsvg-convert not found (install librsvg)", file=sys.stderr)
        sys.exit(1)

    DOCS_IMAGES.mkdir(parents=True, exist_ok=True)
    await _capture_run_mode("run-mode")
    await _capture_run_mode("hero")
    await _capture_joker_pick()
    await _capture_classic_mode()


def shutil_which(cmd: str) -> str | None:
    from shutil import which

    return which(cmd)


if __name__ == "__main__":
    _ensure_capture_env()
    sys.path.insert(0, str(REPO_ROOT))
    asyncio.run(main())
