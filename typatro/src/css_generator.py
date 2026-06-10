from pathlib import Path

from platformdirs import user_cache_dir, user_config_dir

TARGET_FOLDER = Path(user_cache_dir("typatro"))
TARGET_FILE = TARGET_FOLDER / "styles.tcss"

# Balatro variables with fallbacks for themes that don't define them
BALATRO_VARIABLE_DEFAULTS = {
    "$chips-color": "#0093ff",
    "$mult-color": "#fe5f55",
    "$gold-color": "#eac058",
    "$card-bg": "#f4f4f4",
    "$card-text": "#1e2b3c",
}


def _missing_variable_defaults(theme_css: str) -> str:
    """Build CSS variable declarations for Balatro vars missing from a theme."""
    lines = []
    for var, default in BALATRO_VARIABLE_DEFAULTS.items():
        if f"{var}:" not in theme_css:
            lines.append(f"{var}: {default};")
    if not lines:
        return ""
    return "\n".join(lines) + "\n"


def write_css_file(theme_css: str, base_css: str) -> None:
    if not TARGET_FILE.exists():
        TARGET_FOLDER.mkdir(parents=True, exist_ok=True)

    with open(TARGET_FILE, "w") as target:
        target.write(theme_css)
        target.write(_missing_variable_defaults(theme_css))
        target.write(base_css)


def generate_theme_file(theme: str) -> None:
    """
    Theme generator which merges theme and base CSS files

    Args:
        theme (str): theme name
    """
    css_folder = Path.absolute(Path(__file__).parent.parent) / "ui" / "css"
    base_path = css_folder / "base.tcss"
    with open(base_path, "r") as base_file:
        base_css = base_file.read()

    def get_theme_path():
        user_themes_folder = Path(user_config_dir("typatro")) / "themes"
        user_theme_path = user_themes_folder / f"{theme}.tcss"

        if user_theme_path.exists():
            return user_theme_path

        base_themes_folder = css_folder / "themes"
        base_theme_path = base_themes_folder / f"{theme}.tcss"

        return base_theme_path

    with open(get_theme_path(), "r") as theme_file:
        theme_css = theme_file.read()

    write_css_file(theme_css, base_css)
