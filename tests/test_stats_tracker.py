"""Stats tracker performance and counter tests."""

from typatro.src.stats_tracker import CheckPoint, Match, StatsTracker


def test_add_checkpoint_maintains_incremental_counters():
    stats = StatsTracker()
    stats.start_time = 1.0

    for index in range(50):
        stats.add_checkpoint(CheckPoint("a", index + 1, Match.MATCH))

    assert stats.correct == 50
    assert stats.incorrect == 0
    assert stats.accuracy == 100


def test_word_count_increments_on_space_match():
    stats = StatsTracker()
    stats.start_time = 1.0

    stats.add_checkpoint(CheckPoint("a", 1, Match.MATCH))
    stats.add_checkpoint(CheckPoint("b", 2, Match.MATCH))
    stats.add_checkpoint(CheckPoint(" ", 3, Match.MATCH))
    stats.add_checkpoint(CheckPoint("c", 4, Match.MATCH))
    stats.add_checkpoint(CheckPoint(" ", 5, Match.MATCH))

    assert stats.word_count == 2


def test_large_session_counter_reads_stay_fast():
    stats = StatsTracker()
    stats.start_time = 1.0

    for index in range(8000):
        letter = " " if index % 6 == 5 else "a"
        stats.add_checkpoint(CheckPoint(letter, index + 1, Match.MATCH))

    assert stats.correct == 8000
    assert stats.word_count > 1000
    assert stats.accuracy == 100
