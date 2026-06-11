"""Persistent run state for Balatro ante/blind/joker progression."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import platformdirs
from json import dump, load

from typatro.src.blind import (
    BlindDef,
    BossBlind,
    apply_boss_debuff,
    clear_boss_debuffs,
    compute_target,
    get_blind_for_index,
)
from typatro.src.jokers import MAX_JOKERS, JokerDef, get_joker_by_id, jokers_from_ids
from typatro.src.parser import config_parser


@dataclass
class RunState:
    ante: int = 1
    blind_index: int = 0
    joker_ids: List[str] = field(default_factory=list)
    game_mode: str = "run"  # "run" or "classic"
    total_score: int = 0

    @property
    def jokers(self) -> List[JokerDef]:
        return jokers_from_ids(self.joker_ids)

    @property
    def current_blind(self) -> BlindDef:
        return get_blind_for_index(self.blind_index, self.ante)

    def target_score(self) -> int:
        word_count = self._word_count()
        blind = self.current_blind
        target = compute_target(blind, word_count, self.ante)
        if blind.boss and blind.boss == BossBlind.THE_WALL:
            target = target * 13 // 10
        return target

    def _word_count(self) -> int:
        mode = config_parser.get("mode")
        if mode == "words":
            return config_parser.get("words_count")
        minutes = config_parser.get("time_count") / 60
        return round(600 * minutes)

    def apply_blind_debuffs(self) -> None:
        apply_boss_debuff(self.current_blind.boss)

    def advance_blind(self, score: int) -> bool:
        """Advance to next blind if score met target. Returns True if blind beaten."""
        if score < self.target_score():
            return False

        self.total_score += score
        self.blind_index += 1

        if self.blind_index >= 3:
            self.blind_index = 0
            self.ante += 1

        return True

    def add_joker(self, joker_id: str) -> bool:
        if len(self.joker_ids) >= MAX_JOKERS:
            return False
        if joker_id not in self.joker_ids:
            self.joker_ids.append(joker_id)
        return True

    def reset_run(self) -> None:
        self.ante = 1
        self.blind_index = 0
        self.joker_ids = []
        self.total_score = 0

    def to_dict(self) -> dict:
        return {
            "ante": self.ante,
            "blind_index": self.blind_index,
            "joker_ids": self.joker_ids,
            "game_mode": self.game_mode,
            "total_score": self.total_score,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RunState":
        return cls(
            ante=data.get("ante", 1),
            blind_index=data.get("blind_index", 0),
            joker_ids=data.get("joker_ids", []),
            game_mode=data.get("game_mode", "run"),
            total_score=data.get("total_score", 0),
        )


class RunStateManager:
    """Load/save run state to disk."""

    def __init__(self) -> None:
        self.config_path = Path(platformdirs.user_config_dir("typatro"))
        self.file_path = self.config_path / "run.json"
        self.state = self.load()
        self._app = None

    def set_active_app(self, app) -> None:
        """Bind the running TUI so reset can refresh sidebar widgets."""
        self._app = app

    def load(self) -> RunState:
        if not self.file_path.exists():
            return RunState()
        with open(self.file_path, "r") as fp:
            return RunState.from_dict(load(fp))

    def save(self) -> None:
        self.config_path.mkdir(parents=True, exist_ok=True)
        with open(self.file_path, "w") as fp:
            dump(self.state.to_dict(), fp)

    def reset(self) -> RunState:
        self.state.reset_run()
        clear_boss_debuffs()
        self.save()
        self._refresh_ui()
        return self.state

    def _refresh_ui(self) -> None:
        if self._app is None:
            return
        try:
            from typatro.ui.widgets import Space
            from typatro.ui.widgets.balatro import JokerRow

            main = self._app.get_screen("main")
            main.query_one(Space).reset_components()
            main.query_one(JokerRow).update_jokers(self.state.jokers)
        except Exception:
            pass


run_manager = RunStateManager()
