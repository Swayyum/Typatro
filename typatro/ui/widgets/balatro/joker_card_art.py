"""Balatro-style joker card rendering for Rich / Textual.

Balatro jokers are white playing cards with centered art, a name plate,
and an effect line where Mult is red and Chips are blue. Those colors are
part of the card identity, so they are fixed here rather than themed.
"""

from __future__ import annotations

from rich.style import Style
from rich.text import Text

from typatro.src.jokers import JokerDef, JokerEffect

CARD_BG = "#f6f1e3"
CARD_TEXT = "#33272e"
CARD_EDGE = "#d8cfba"
MULT_RED = "#fe5f55"
CHIPS_BLUE = "#0093ff"
GOLD = "#eac058"

# Pick-screen card size (portrait-ish in terminal cells).
CARD_WIDTH = 28
CARD_HEIGHT = 11

_MULT_EFFECTS = frozenset(
    {
        JokerEffect.FLAT_MULT,
        JokerEffect.MULT_ON_PERFECT_WORD,
        JokerEffect.MULT_ACCURACY,
    }
)

FRAME_STYLE = Style(color=CARD_EDGE, bgcolor=CARD_BG)
ICON_STYLE = Style(color=MULT_RED, bgcolor=CARD_BG, bold=True)
NAME_STYLE = Style(color=CARD_TEXT, bgcolor=CARD_BG, bold=True)
BODY_STYLE = Style(bgcolor=CARD_BG)
MULT_STYLE = Style(color=MULT_RED, bgcolor=CARD_BG, bold=True)
CHIPS_STYLE = Style(color=CHIPS_BLUE, bgcolor=CARD_BG, bold=True)
HINT_STYLE = Style(color="#8d8478", bgcolor=CARD_BG, italic=True)
PIP_STYLE = Style(color=GOLD, bgcolor=CARD_BG)


def effect_style(joker: JokerDef) -> Style:
    return MULT_STYLE if joker.effect in _MULT_EFFECTS else CHIPS_STYLE


def _cell_len(text: str) -> int:
    return Text(text).cell_len


def _truncate(text: str, width: int) -> str:
    """Truncate plain text to fit ``width`` terminal cells."""
    text = text.strip()
    if _cell_len(text) <= width:
        return text
    truncated = Text(text)
    truncated.truncate(width, overflow="ellipsis")
    return truncated.plain


def _framed_row(card: Text, inner: int, content: Text | None = None) -> None:
    card.append("▌", style=FRAME_STYLE)
    content_cells = content.cell_len if content is not None else 0
    left = (inner - content_cells) // 2
    right = inner - content_cells - left
    card.append(" " * left, style=BODY_STYLE)
    if content is not None:
        card.append_text(content)
    card.append(" " * right, style=BODY_STYLE)
    card.append("▐\n", style=FRAME_STYLE)


def _corner_pips(inner: int, icon: str) -> Text:
    """Corner pip row sized in terminal cells (wide emoji-safe)."""
    icon_cells = _cell_len(icon)
    pips = Text()
    pips.append(icon, style=PIP_STYLE)
    pad = max(0, inner - 2 * icon_cells)
    pips.append(" " * pad, style=BODY_STYLE)
    pips.append(icon, style=PIP_STYLE)
    return pips


def render_joker_card(
    joker: JokerDef,
    width: int,
    *,
    index_label: str | None = None,
    phase: float = 0.0,
    screen_x: int = 0,
    screen_y: int = 0,
) -> Text:
    """Render a Balatro-style pick card — clean text layout for every joker."""
    del phase, screen_x, screen_y
    return _render_text_joker_card(joker, width, index_label=index_label)


def _render_text_joker_card(
    joker: JokerDef,
    width: int,
    *,
    index_label: str | None = None,
) -> Text:
    """Render a text/emoji joker pick card."""
    inner = width - 2
    card = Text()

    card.append("▗" + "▄" * inner + "▖\n", style=FRAME_STYLE)

    card.append("▌", style=FRAME_STYLE)
    card.append_text(_corner_pips(inner, joker.icon))
    card.append("▐\n", style=FRAME_STYLE)

    _framed_row(card, inner)
    _framed_row(card, inner, Text(_truncate(joker.icon, inner), style=ICON_STYLE))
    _framed_row(card, inner)
    _framed_row(card, inner, Text(_truncate(joker.name.upper(), inner), style=NAME_STYLE))
    _framed_row(
        card,
        inner,
        Text("·" * min(inner - 4, 14), style=Style(color=CARD_EDGE, bgcolor=CARD_BG)),
    )
    _framed_row(
        card,
        inner,
        Text(_truncate(joker.description, inner), style=effect_style(joker)),
    )
    if index_label:
        _framed_row(card, inner, Text(index_label, style=HINT_STYLE))
    _framed_row(card, inner)

    card.append("▝" + "▀" * inner + "▘", style=FRAME_STYLE)
    return card


def render_joker_sidebar_entry(
    joker: JokerDef,
    width: int,
    *,
    icon_style: Style,
    name_style: Style,
    mult_style: Style,
    chips_style: Style,
    muted_style: Style,
    slot: int | None = None,
) -> Text:
    """Two-line sidebar entry: slot, icon, name, then full effect on line two."""
    text = Text()
    desc_style = mult_style if joker.effect in _MULT_EFFECTS else chips_style

    slot_prefix = f"{slot} " if slot is not None else ""
    slot_cells = _cell_len(slot_prefix)
    icon_part = f"{joker.icon} "
    icon_cells = _cell_len(icon_part)
    name_budget = max(6, width - slot_cells - icon_cells)
    name = _truncate(joker.name, name_budget)

    text.append(slot_prefix, style=muted_style)
    text.append(icon_part, style=icon_style)
    text.append(name, style=name_style)
    text.append("\n")

    indent_cells = slot_cells + icon_cells
    desc_budget = max(8, width - indent_cells)
    desc = _truncate(joker.description, desc_budget)
    text.append(" " * indent_cells, style=muted_style)
    text.append(desc, style=desc_style)
    return text


def render_joker_line(joker: JokerDef, width: int) -> Text:
    """Single-line fallback using pick-screen colors (tests / legacy)."""
    return render_joker_sidebar_entry(
        joker,
        width,
        icon_style=ICON_STYLE,
        name_style=NAME_STYLE,
        mult_style=MULT_STYLE,
        chips_style=CHIPS_STYLE,
        muted_style=HINT_STYLE,
    )
