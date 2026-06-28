
def test_joker_image_assets_present():
    from typatro.src.joker_image import JOKER_IMAGE_FILES, joker_image_path, prebaked_art_path

    for joker_id, filename in JOKER_IMAGE_FILES.items():
        path = joker_image_path(joker_id)
        assert path is not None, f"missing asset for {joker_id} ({filename})"
        assert path.is_file()
        art = prebaked_art_path(joker_id)
        assert art is not None, f"missing pre-baked art for {joker_id}"
        assert art.is_file()


PREBAKED_WIDTH = 34
PREBAKED_ROWS = 12


def test_load_prebaked_art_lines():
    from typatro.src.joker_image import load_prebaked_art_lines

    for joker_id in ("joker", "greedy", "banner", "mystic"):
        lines = load_prebaked_art_lines(joker_id, PREBAKED_WIDTH, PREBAKED_ROWS)
        assert lines is not None, joker_id
        assert len(lines) == PREBAKED_ROWS
        for line in lines:
            assert line.cell_len == PREBAKED_WIDTH


def test_prebaked_art_has_color_variety():
    from typatro.src.joker_image import load_prebaked_art_lines

    lines = load_prebaked_art_lines("banner", PREBAKED_WIDTH, PREBAKED_ROWS)
    assert lines is not None
    colors: set[str] = set()
    for line in lines:
        for *_, style in line._spans:
            for attr in ("color", "bgcolor"):
                value = getattr(style, attr, None)
                if value is not None:
                    colors.add(str(value))
    assert len(colors) >= 12


def test_prebaked_art_uses_block_symbols_not_half_blocks():
    from typatro.src.joker_image import load_prebaked_art_lines

    lines = load_prebaked_art_lines("joker", PREBAKED_WIDTH, PREBAKED_ROWS)
    assert lines is not None
    plain = "".join(line.plain for line in lines)
    assert "▀" not in plain
    assert any(ch in plain for ch in "▁▂▃▄▅▆▇█▏▕▔▖▗▘▝▞")


def test_render_joker_art_lines_dimensions():
    from typatro.src.joker_image import render_joker_art_lines

    width, rows = 26, 8
    lines = render_joker_art_lines("joker", width, rows, phase=0.0)
    assert lines is not None
    assert len(lines) == rows
    for line in lines:
        assert line.cell_len == width


def test_render_joker_art_has_color_variety():
    from typatro.src.joker_image import render_joker_art_lines

    lines = render_joker_art_lines("banner", 26, 8, phase=0.0)
    assert lines is not None
    hex_colors = set()
    for line in lines:
        for *_, style in line._spans:
            if not style:
                continue
            token = str(getattr(style, "color", style))
            if "#" in token:
                hex_colors.add(token.split()[0])
    assert len(hex_colors) >= 8, "art should show multiple sampled hues"


def test_render_joker_art_uses_half_blocks():
    from typatro.src.joker_image import render_joker_art_lines

    lines = render_joker_art_lines("mystic", 26, 4, phase=0.0)
    assert lines is not None
    plain = "".join(line.plain for line in lines)
    assert "▀" in plain
    assert not any("\u2800" <= ch <= "\u28ff" for ch in plain)


def test_render_joker_art_not_dense_dot_grid():
    """Bundled JPEGs must not collapse into a uniform braille dot screen."""
    from typatro.src.joker_image import render_joker_art_lines

    for joker_id in ("joker", "greedy", "banner"):
        lines = render_joker_art_lines(joker_id, 26, 8, phase=0.0)
        assert lines is not None
        plain = "".join(line.plain for line in lines)
        assert not any("\u2800" <= ch <= "\u28ff" for ch in plain), (
            f"{joker_id} still renders as braille dots"
        )

        fg_bg_pairs: set[tuple[str, str]] = set()
        for line in lines:
            for *_, style in line._spans:
                fg = getattr(style, "color", None)
                bg = getattr(style, "bgcolor", None)
                if fg is not None and bg is not None:
                    fg_bg_pairs.add((str(fg), str(bg)))
        assert len(fg_bg_pairs) >= 16, (
            f"{joker_id} art lacks distinct fg/bg color pairs"
        )


def test_joker_art_has_edge_detail():
    """Sampled fallback art must retain horizontal edges, not a flat color slab."""
    from typatro.src.joker_image import art_color_variance

    for joker_id in ("joker", "greedy", "banner", "mystic"):
        transitions = art_color_variance(joker_id, 26, 8)
        assert transitions >= 80, f"{joker_id} art looks too uniform ({transitions} edges)"


def test_terminal_image_protocol_detection(monkeypatch):
    from typatro.src.joker_image import terminal_image_protocol

    monkeypatch.delenv("KITTY_WINDOW_ID", raising=False)
    monkeypatch.setenv("TERM_PROGRAM", "iTerm.app")
    assert terminal_image_protocol() is None

    monkeypatch.setenv("TYPATRO_INLINE_IMAGES", "1")
    assert terminal_image_protocol() == "iterm"

    monkeypatch.setenv("TERM_PROGRAM", "kitty")
    assert terminal_image_protocol() == "kitty"

    monkeypatch.setenv("TERM_PROGRAM", "Apple_Terminal")
    monkeypatch.setenv("TERM_PROGRAM_VERSION", "455.1")
    assert terminal_image_protocol() == "iterm"

    monkeypatch.delenv("TERM_PROGRAM_VERSION", raising=False)
    monkeypatch.setenv("TERM_PROGRAM", "vscode")
    assert terminal_image_protocol() is None


def test_render_joker_terminal_art_emits_control_sequence(monkeypatch):
    from rich.console import Console

    from typatro.src.joker_image import render_joker_terminal_art

    monkeypatch.setenv("TYPATRO_INLINE_IMAGES", "1")
    monkeypatch.setenv("TERM_PROGRAM", "kitty")
    art = render_joker_terminal_art(
        "joker",
        PREBAKED_WIDTH,
        PREBAKED_ROWS,
        screen_x=10,
        screen_y=5,
    )
    assert art is not None

    console = Console(width=80, force_terminal=True, color_system="truecolor")
    segments = list(art.__rich_console__(console, console.options))
    control = [segment for segment in segments if segment.control]
    assert control, "terminal art should include a graphics control sequence"
    assert "\x1b_G" in control[0].text


def test_render_joker_card_uses_text_layout_for_image_jokers():
    from typatro.src.jokers import get_joker_by_id
    from typatro.ui.widgets.balatro.joker_card_art import CARD_WIDTH, render_joker_card

    joker = get_joker_by_id("greedy")
    assert joker is not None
    card = render_joker_card(joker, CARD_WIDTH, index_label="[ 1 ]")
    plain = _renderable_plain(card)
    assert "GREEDY JOKER" in plain.upper() or "GREEDY" in plain.upper()
    assert "+2 Mult" in plain
    assert "♦" in plain


def _renderable_plain(renderable) -> str:
    from rich.console import Console

    console = Console(
        width=120,
        force_terminal=True,
        color_system="truecolor",
        record=True,
    )
    console.print(renderable)
    return console.export_text(clear=False).rstrip("\n")


def test_render_joker_card_text_layout(monkeypatch):
    from typatro.src.jokers import get_joker_by_id
    from typatro.ui.widgets.balatro.joker_card_art import CARD_HEIGHT, CARD_WIDTH, render_joker_card

    joker = get_joker_by_id("greedy")
    assert joker is not None
    card = render_joker_card(joker, CARD_WIDTH, index_label="[ 1 ]")
    plain = _renderable_plain(card)
    assert "[ 1 ]" in plain
    assert "▗" in plain
    assert plain.count("\n") + 1 == CARD_HEIGHT
    assert "♦" in plain
