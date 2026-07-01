from time import time
from dataclasses import dataclass
from enum import Enum
from typing import List


class Match(Enum):
    """
    Match enum class for character match
    """

    MATCH = 1
    MISMATCH = 2
    BACKSPACE = 3
    SKIPPED = 4


@dataclass
class CheckPoint:
    """
    Checkpoint class to maintain record of position and elapsed time at that point
    """

    letter: str
    position: int
    correct: Match

    def add_elapsed(self, elapsed) -> None:
        self.elapsed = elapsed


class StatsTracker:
    """
    Tracker class to calculate stats while typing
    """

    def __init__(self) -> None:
        self.reset()

    def get_checkpoints_last_word(self) -> List[CheckPoint]:
        if not self.checkpoints:
            return []

        end = len(self.checkpoints) - 1
        while end >= 0 and self.checkpoints[end].letter == " ":
            end -= 1
        if end < 0:
            return []

        start = end
        while start >= 0 and self.checkpoints[start].letter != " ":
            start -= 1
        return self.checkpoints[start + 1 : end + 1]

    @property
    def elapsed_time(self) -> float:
        if not self.start_time:
            raise ValueError("Start time not set")

        if self.end_time:
            return self.end_time - self.start_time

        return time() - self.start_time

    @property
    def word_count(self) -> int:
        self._ensure_counter_sync()
        return self._word_count

    @property
    def last_word_accuracy(self) -> int:
        correct = 0
        incorrect = 0

        checkpoints = self.get_checkpoints_last_word()

        if not checkpoints:
            raise ValueError("No checkpoints")

        for i in checkpoints:
            correct += i.correct == Match.MATCH
            incorrect += i.correct == Match.MISMATCH

        total = correct + incorrect
        if total == 0:
            raise ValueError("No typed characters in last word")

        return round((correct / total) * 100)

    @property
    def last_word_wpm(self) -> int:
        checkpoints = self.get_checkpoints_last_word()

        if not checkpoints:
            raise ValueError("No checkpoints")

        start = checkpoints[0].elapsed
        stop = checkpoints[-1].elapsed
        elapsed = stop - start

        if elapsed == 0:
            raise ValueError("Elapsed time is 0")

        raw = 60 / elapsed
        return round(self.last_word_accuracy * raw / 100)

    @property
    def raw_wpm(self) -> int:
        time_taken = self.elapsed_time / 60
        return int(self.word_count / time_taken)

    @property
    def accuracy(self) -> int:
        self._ensure_counter_sync()
        total_typed = self._match_count + self._mismatch_count

        if total_typed == 0:
            return 0

        return int((self._match_count / total_typed) * 100)

    @property
    def wpm(self) -> int:
        return int(self.raw_wpm * (self.accuracy / 100))

    @property
    def correct(self) -> int:
        self._ensure_counter_sync()
        return self._match_count

    @property
    def incorrect(self) -> int:
        self._ensure_counter_sync()
        return self._mismatch_count

    @property
    def missed(self) -> int:
        return sum(
            checkpoint.correct == Match.SKIPPED for checkpoint in self.checkpoints
        )

    # ---------------------------------------

    def reset(self) -> None:
        self.start_time = None
        self.end_time = None
        self.checkpoints: List[CheckPoint] = []
        self._match_count = 0
        self._mismatch_count = 0
        self._word_count = 0
        self._counter_synced_len = 0

    def finish(self) -> None:
        self.end_time = time()

    def _ensure_counter_sync(self) -> None:
        if self._counter_synced_len == len(self.checkpoints):
            return
        self._match_count = sum(
            checkpoint.correct == Match.MATCH for checkpoint in self.checkpoints
        )
        self._mismatch_count = sum(
            checkpoint.correct == Match.MISMATCH for checkpoint in self.checkpoints
        )
        self._word_count = sum(
            checkpoint.letter == " " and checkpoint.correct == Match.MATCH
            for checkpoint in self.checkpoints
        )
        self._counter_synced_len = len(self.checkpoints)

    def add_checkpoint(self, checkpoint: CheckPoint) -> None:
        if not self.start_time:
            self.start_time = time()

        elapsed = time() - self.start_time
        checkpoint.add_elapsed(elapsed)

        self.checkpoints.append(checkpoint)
        if checkpoint.correct == Match.MATCH:
            self._match_count += 1
            if checkpoint.letter == " ":
                self._word_count += 1
        elif checkpoint.correct == Match.MISMATCH:
            self._mismatch_count += 1
        self._counter_synced_len = len(self.checkpoints)
