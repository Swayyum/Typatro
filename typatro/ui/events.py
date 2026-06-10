from typing import Optional

from textual.message import Message

from typatro.src import StatsTracker
from typatro.src.jokers import JokerDef
from typatro.src.scoring import ScoreState


class SetScreen(Message):
    """
    Emitted to change the screen content
    """

    def __init__(self, screen_name: str) -> None:
        super().__init__()
        self.screen_name = screen_name


class ShowResults(Message):
    """
    Emitted when the typing is finished
    """

    def __init__(
        self,
        stats: StatsTracker,
        failed: bool = False,
        score_state: Optional[ScoreState] = None,
        target_score: int = 0,
        blind_beaten: bool = False,
    ) -> None:
        super().__init__()
        self.stats = stats
        self.failed = failed
        self.score_state = score_state
        self.target_score = target_score
        self.blind_beaten = blind_beaten


class JokerSelected(Message):
    """Emitted when player picks a joker from the choice screen."""

    def __init__(self, joker: JokerDef) -> None:
        super().__init__()
        self.joker = joker
