import webbrowser
from textual import on
from textual.app import App, ComposeResult, events
from textual.screen import Screen
from textual.widgets import ContentSwitcher
from typatro.ui.events import SetScreen, ShowResults
from typatro.ui.widgets import *  # noqa
from typatro.ui.screens import *  # noqa
from typatro.ui.widgets.palette.palette_list import ApplyLanguage, ApplyTheme
from typatro.ui.widgets.palette import LanguagePalette, ThemePalette
from typatro.src import config_parser, generate_theme_file, data_parser, TARGET_FILE, run_manager
from typatro.ui.widgets import Space, Ticker
from typatro.ui.screens.confirm import ConfirmScreen
from typatro.ui.screens.joker_choice import JokerChoiceScreen
from typatro.src.jokers import JokerDef


class MainScreen(Screen):
    """
    Main Screen which renders all the first visible option when app starts
    """

    DEFAULT_CSS = """
    MainScreen {
        layout: grid;
        grid-size: 1 2;
        grid-rows: 5 1fr;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._pending_joker_pick = False

    def compose(self) -> ComposeResult:
        yield Header()
        yield ContentSwitcher(
            TypingScreen(id="typing"),
            AboutScreen(id="about"),
            SettingsScreen(id="settings"),
            HelpScreen(id="help"),
            ResultScreen(id="result"),
            # initial screen
            initial="typing",
        )

    @on(SetScreen)
    def screen_change(self, event: SetScreen) -> None:
        """
        Change BaseWidget in the main screen depending on name

        Args:
            event (SetScreen): event with screen name
        """

        self.query_one(ContentSwitcher).current = event.screen_name
        self.query_one(Header).set_active(event.screen_name)

    @on(ShowResults)
    def show_results(self, event: ShowResults) -> None:
        """
        Triggered when typing is finished

        Args:
            event (ShowResults): Event containing stats and if it the typing was a failed attempt
        """

        # reset all watching timers
        space = self.query_one(Space)
        space.check_timer.pause()
        space.tracker.stats.finish()
        self.query_one(Ticker).reset()

        self.query_one(ContentSwitcher).current = "result"
        self.query_one(ResultScreen).set_results(
            event.stats,
            score_state=event.score_state,
            target_score=event.target_score,
            blind_beaten=event.blind_beaten,
            failed=event.failed,
        )

        data_parser.add_stats(event.stats, event.failed)

        if event.blind_beaten and config_parser.get("game_mode") == "run":
            self._pending_joker_pick = True

    def offer_joker_pick(self) -> None:
        """Push the joker choice screen; applies the pick via callback."""

        def on_pick(result) -> None:
            if result and isinstance(result, JokerDef):
                run_manager.state.add_joker(result.id)
                run_manager.save()
                try:
                    from typatro.ui.widgets.balatro import JokerRow

                    self.query_one(JokerRow).update_jokers(run_manager.state.jokers)
                except Exception:
                    pass

            # Re-reset so the scoring engine picks up new jokers and blind
            self.query_one(Space).reset()

        exclude = run_manager.state.joker_ids
        self.app.push_screen(JokerChoiceScreen(exclude_ids=exclude), on_pick)

    async def handle_key(self, event: events.Key) -> bool:
        visible = self.query_one(ContentSwitcher).visible_content
        if visible:
            await visible.handle_key(event)

        return True


class Typatro(App):
    CSS_PATH = str(TARGET_FILE)
    SCREENS = {
        "main": MainScreen,
        "theme": ThemePaletteScreen,
        "language": LanguagePaletteScreen,
        "confirm": ConfirmScreen,
        "joker_choice": JokerChoiceScreen,
    }

    def __init__(self, *args, **kwargs) -> None:
        self._pending_joker_pick = False
        self.action_theme(config_parser.get("theme"))
        super().__init__(*args, **kwargs, watch_css=True)

    async def _on_css_change(self) -> None:
        await super()._on_css_change()
        self.refresh_css()

    async def on_mount(self) -> None:
        self.push_screen("main")
        run_manager.set_active_app(self)

    @on(ApplyLanguage)
    def apply_language(self, event: ApplyLanguage) -> None:
        config_parser.set("language", event.value)
        self.app.get_screen("main").query_one(LanguagePalette).refresh()
        self.app.get_screen("main").query_one(Space).reset()

    @on(ApplyTheme)
    def apply_theme(self, event: ApplyTheme) -> None:
        self.action_theme(event.value)
        config_parser.set("theme", event.value)
        self.app.get_screen("main").query_one(ThemePalette).refresh()

    def action_star(self) -> None:
        webbrowser.open("https://github.com/Swayyum/Typatro")

    def action_theme(self, theme: str) -> None:
        generate_theme_file(theme)

