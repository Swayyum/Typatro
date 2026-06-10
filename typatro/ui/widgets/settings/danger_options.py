from typatro.src.parser import config_parser
from typatro.src import run_manager
from .option import BaseOption, Confirm


class ResetConfig(Confirm):
    def __init__(self) -> None:
        def callback():
            config_parser.reset()
            for setting in self.screen.query(BaseOption):
                setting.load_current_setting()
                setting.refresh()

        super().__init__("rest_config", "Reset", callback)


class ResetRun(Confirm):
    def __init__(self) -> None:
        def callback():
            run_manager.reset()

        super().__init__("reset_run", "Reset Run", callback)
