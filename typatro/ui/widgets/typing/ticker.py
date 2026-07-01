from textual.widget import Widget
from typatro.src import config_parser


class Ticker(Widget):
    """
    Ticker widget to show time/word left
    """

    TICK_INTERVAL = 0.5

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.update_check = self.set_interval(self.TICK_INTERVAL, self.update, pause=True)
        self._space = None
        self.reset()

    def on_mount(self) -> None:
        try:
            from typatro.ui.widgets import Space

            self._space = self.screen.query_one(Space)
        except Exception:
            self._space = None

    def update(self) -> None:
        from typatro.ui.widgets import Space

        space = self._space
        if space is None:
            try:
                space = self.screen.query_one(Space)
                self._space = space
            except Exception:
                return

        mode = config_parser.get("mode")
        stats = space.tracker.stats

        if not stats.start_time:
            return

        if mode == "words":
            count = config_parser.get("words_count")
            words_typed = stats.word_count
            new_text = f"{words_typed}/{count}"
        else:
            count = config_parser.get("time_count")
            time_remaining = count - stats.elapsed_time
            if time_remaining <= 0:
                return space.finish_typing(fail=False)

            new_text = str(round(time_remaining))

        if new_text == self.text:
            return

        self.text = new_text
        self.refresh()

    def reset(self) -> None:
        self.update_check.pause()
        mode = config_parser.get("mode")
        if mode == "words":
            count = config_parser.get("words_count")
            self.text = f"0/{count}"
        else:
            count = config_parser.get("time_count")
            self.text = str(count)

        self.refresh()

    def render(self) -> str:
        return self.text
