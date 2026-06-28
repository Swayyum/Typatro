import os
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widget import Widget

from typatro.ui.sidebar_layout import SIDEBAR_INNER_WIDTH, SIDEBAR_PADDING, SIDEBAR_WIDTH
from typatro.ui.widgets.label import Banner, NavItem


def get_username() -> str:
    try:
        username = os.getlogin()
    except OSError:
        uid = os.getuid()
        import pwd

        username = pwd.getpwuid(uid).pw_name

    return username


class HeaderBrandColumn(Widget):
    """Matches ``GameSidebar`` width/padding so the logo aligns with panel borders."""

    DEFAULT_CSS = f"""
    HeaderBrandColumn {{
        width: 100%;
        height: 100%;
        padding: 0 {SIDEBAR_PADDING};
    }}

    HeaderBrandColumn > Banner {{
        width: 100%;
        min-width: {SIDEBAR_INNER_WIDTH};
        height: 100%;
        content-align: center middle;
        padding: 0;
    }}
    """


class Header(Widget):
    """
    Header which forms the top banner of the app
    """

    DEFAULT_CSS = f"""
    Header {{
        layout: grid;
        grid-size: 2 1;
        grid-rows: 5;
        grid-columns: {SIDEBAR_WIDTH} 1fr;
    }}

    Header > Horizontal {{
        align: right middle;
        height: 100%;
    }}
    """

    def on_resize(self) -> None:
        # XXX: Why use screen size and not widget size?
        # Ans: Because this can change the widget size (be it header or container)
        #      which will trigger this method again, causing an infinite loop
        height = self.screen.size.height

        # NOTE: This seems like a good ratio (5:30) to enable/disable tall mode
        if height < 30:
            self.disable_tall_mode()
        else:
            self.enable_tall_mode()

        self.refresh(layout=True)

    def enable_tall_mode(self) -> None:
        if self.styles.height == 5:
            return

        self.styles.height = 5
        self.query_one(Banner).is_tall = True
        self.query_one("Header > Horizontal").styles.height = "5"

    def disable_tall_mode(self) -> None:
        if self.styles.height == 3:
            return

        self.styles.height = 3
        self.query_one(Banner).is_tall = False
        self.query_one("Header > Horizontal").styles.height = "3"

    def set_active(self, name: str) -> None:
        for i in self.query(NavItem):
            i.set_class(i.screen_name == name, "active")

    def compose(self) -> ComposeResult:
        with HeaderBrandColumn():
            yield Banner("typatro")

        with Horizontal():
            home = NavItem("󰌌 home", "typing")
            home.add_class("active")

            yield home
            yield NavItem(" settings", "settings")
            yield NavItem("󰋗 help", "help")
            yield NavItem(" about", "about")

        # yield NavItem("  " + get_username())
