#!/usr/bin/env python3
"""Generate pre-baked terminal art for bundled joker JPEGs using chafa.

Run from repo root after changing JPEG assets::

    python scripts/generate_joker_art.py

Requires ``chafa`` on PATH (https://github.com/hpjansson/chafa).
Output: ``typatro/assets/jokers/<id>.art.json`` — committed to the repo so
installers on any OS get identical card art without chafa at runtime.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from rich.style import Style
from rich.text import Text

REPO_ROOT = Path(__file__).resolve().parents[1]
JOKERS_DIR = REPO_ROOT / "typatro" / "assets" / "jokers"

# Must match pick-screen interior (CARD_WIDTH - 2, ART_ROWS).
CHAFA_SIZE = "34x24"
ART_WIDTH = 34
ART_ROWS = 12
CARD_BG = "f6f1e3"

JOKER_STEMS = {
    "joker": "joker",
    "greedy": "greedy",
    "lusty": "lusty",
    "wrathful": "wrathful",
    "banner": "banner",
    "mystic": "mystic",
}

_CURSOR_RE = re.compile(r"\x1b\[\?25[lh]")


def _color_to_hex(value) -> str | None:
    if value is None:
        return None
    triplet = getattr(value, "triplet", None)
    if triplet is not None:
        return f"#{triplet.red:02x}{triplet.green:02x}{triplet.blue:02x}"
    text = str(value)
    if text.startswith("#"):
        return text
    return None


def _style_hex(style: Style | None, attr: str) -> str | None:
    if style is None:
        return None
    return _color_to_hex(getattr(style, attr, None))


def _line_to_row(line: Text) -> list[list[str | None]]:
    style_at: dict[int, Style] = {}
    for span in line._spans:
        for offset in range(span.start, span.end):
            style_at[offset] = span.style
    row: list[list[str | None]] = []
    for offset, char in enumerate(line.plain):
        style = style_at.get(offset)
        row.append([char, _style_hex(style, "color"), _style_hex(style, "bgcolor")])
    return row


def _text_to_rows(text: Text) -> list[list[list[str | None]]]:
    """Serialize Rich Text spans into rows of [char, fg, bg] cells."""
    rows: list[list[list[str | None]]] = []
    for line in text.split("\n", allow_blank=True):
        if not line.plain and not line._spans:
            continue
        rows.append(_line_to_row(line))
    return rows



def run_chafa(jpeg_path: Path) -> str:
    cmd = [
        "chafa",
        "-s",
        CHAFA_SIZE,
        "--symbols",
        "block",
        "--colors",
        "full",
        "--bg",
        CARD_BG,
        "--animate",
        "off",
        "--polite",
        "on",
        str(jpeg_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return _CURSOR_RE.sub("", result.stdout).strip("\n")


def _decimate_rows(rows: list[list[list[str | None]]]) -> list[list[list[str | None]]]:
    """Pick ``ART_ROWS`` evenly from chafa block output."""
    if len(rows) == ART_ROWS:
        return rows
    if len(rows) < ART_ROWS:
        raise ValueError(f"need at least {ART_ROWS} source rows, got {len(rows)}")
    step = len(rows) / ART_ROWS
    picked = [rows[int(index * step)] for index in range(ART_ROWS)]
    return picked


def ansi_to_rows(ansi: str) -> list[list[list[str | None]]]:
    text = Text.from_ansi(ansi)
    rows = _decimate_rows(_text_to_rows(text))
    if len(rows) != ART_ROWS:
        raise ValueError(f"expected {ART_ROWS} rows, got {len(rows)}")
    for index, row in enumerate(rows):
        if len(row) != ART_WIDTH:
            raise ValueError(
                f"row {index}: expected width {ART_WIDTH}, got {len(row)}"
            )
    return rows


def generate_one(joker_id: str, stem: str) -> None:
    jpeg = JOKERS_DIR / f"{stem}.jpeg"
    if not jpeg.is_file():
        raise FileNotFoundError(jpeg)

    ansi = run_chafa(jpeg)
    rows = ansi_to_rows(ansi)
    payload = {
        "width": ART_WIDTH,
        "height": ART_ROWS,
        "rows": rows,
    }
    out_path = JOKERS_DIR / f"{joker_id}.art.json"
    out_path.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {out_path.relative_to(REPO_ROOT)} ({len(rows)}x{len(rows[0])})")


def main() -> int:
    if shutil.which("chafa") is None:
        print("error: chafa not found on PATH — install from https://github.com/hpjansson/chafa", file=sys.stderr)
        return 1

    for joker_id, stem in JOKER_STEMS.items():
        generate_one(joker_id, stem)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
