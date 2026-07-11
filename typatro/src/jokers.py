"""Joker definitions and scoring modifiers for Balatro run mode."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from random import sample
from typing import List, Optional

from typatro.src.stats_tracker import StatsTracker


class JokerEffect(Enum):
    FLAT_MULT = "flat_mult"
    CHIPS_PER_WORD = "chips_per_word"
    CHIPS_PER_STREAK = "chips_per_streak"
    MULT_ON_PERFECT_WORD = "mult_on_perfect_word"
    CHIPS_LONG_WORD = "chips_long_word"
    CHIPS_CAPITAL = "chips_capital"
    MULT_ACCURACY = "mult_accuracy"
    CHIPS_FLAT = "chips_flat"
    CHIPS_SHORT_WORD = "chips_short_word"
    CHIPS_EXACT_WORD = "chips_exact_word"
    CHIPS_ON_PUNCTUATION = "chips_on_punctuation"
    CHIPS_ON_DIGIT = "chips_on_digit"
    MULT_ON_STREAK_TIER = "mult_on_streak_tier"
    MULT_ON_HIGH_ACCURACY = "mult_on_high_accuracy"
    MULT_ON_WORD_COMPLETE = "mult_on_word_complete"


@dataclass(frozen=True)
class JokerDef:
    id: str
    name: str
    description: str
    effect: JokerEffect
    value: float
    icon: str = "♠"
    word_length: int = 0


# Max streak tiers counted for Streaker (prevents runaway chip growth).
_STREAKER_STREAK_CAP = 5

# Streak length per tier for Ride the Bus-style mult jokers.
_STREAK_TIER_SIZE = 5
_STREAK_TIER_CAP = 5

# Per-keystroke cap on chip bonuses from all jokers combined.
MAX_JOKER_CHIPS_PER_KEYSTROKE = 25

JOKER_ROSTER: List[JokerDef] = [
    JokerDef("joker", "Joker", "+2 Mult", JokerEffect.FLAT_MULT, 2, "♠"),
    JokerDef("greedy", "Greedy Joker", "+2 Mult", JokerEffect.FLAT_MULT, 2, "♦"),
    JokerDef("lusty", "Lusty Joker", "+2 Mult", JokerEffect.FLAT_MULT, 2, "♥"),
    JokerDef("wrathful", "Wrathful Joker", "+2 Mult", JokerEffect.FLAT_MULT, 2, "♣"),
    JokerDef("fibonacci", "Fibonacci", "+4 Chips per word", JokerEffect.CHIPS_PER_WORD, 4, "φ"),
    JokerDef("even_steven", "Even Steven", "+2 Chips per word", JokerEffect.CHIPS_PER_WORD, 2, "2"),
    JokerDef("odd_todd", "Odd Todd", "+10 Chips per word", JokerEffect.CHIPS_PER_WORD, 10, "1"),
    JokerDef("streaker", "Streaker", "+1 Chips per char streak", JokerEffect.CHIPS_PER_STREAK, 1, "⚡"),
    JokerDef("scholar", "Scholar", "+8 Chips on perfect word", JokerEffect.MULT_ON_PERFECT_WORD, 8, "📖"),
    JokerDef("half", "Half Joker", "+8 Chips for 5+ letter words", JokerEffect.CHIPS_LONG_WORD, 8, "½"),
    JokerDef("raised_fist", "Raised Fist", "+5 Chips on capitals", JokerEffect.CHIPS_CAPITAL, 5, "✊"),
    JokerDef("banner", "Banner", "+5 Chips flat", JokerEffect.CHIPS_FLAT, 5, "🏳"),
    JokerDef("mystic", "Mystic Summit", "+0.3 Mult per 10% accuracy", JokerEffect.MULT_ACCURACY, 0.3, "☽"),
    JokerDef("runner", "Runner", "+2 Chips per char streak", JokerEffect.CHIPS_PER_STREAK, 2, "🏃"),
    JokerDef("square", "Square Joker", "+6 Chips on 4-letter words", JokerEffect.CHIPS_EXACT_WORD, 6, "■", word_length=4),
    JokerDef("business", "Business Card", "+8 Chips on punctuation", JokerEffect.CHIPS_ON_PUNCTUATION, 8, "💼"),
    JokerDef("ride_the_bus", "Ride the Bus", "+0.5 Mult per 5 char streak", JokerEffect.MULT_ON_STREAK_TIER, 0.5, "🚌"),
    JokerDef("shortcut", "Shortcut", "+6 Chips on 3-letter words", JokerEffect.CHIPS_SHORT_WORD, 6, "✂️"),
    JokerDef("cloud_9", "Cloud 9", "+2 Mult at 90%+ accuracy", JokerEffect.MULT_ON_HIGH_ACCURACY, 2, "☁"),
    JokerDef("seeing_double", "Seeing Double", "+3 Mult", JokerEffect.FLAT_MULT, 3, "👯"),
    JokerDef("bootstraps", "Bootstraps", "+8 Chips flat", JokerEffect.CHIPS_FLAT, 8, "🥾"),
    JokerDef("flower_pot", "Flower Pot", "+3 Chips per word", JokerEffect.CHIPS_PER_WORD, 3, "🪴"),
    JokerDef("troubadour", "Troubadour", "+10 Chips for 5+ letter words", JokerEffect.CHIPS_LONG_WORD, 10, "🎵"),
    JokerDef("smiley", "Smiley Face", "+6 Chips on digits", JokerEffect.CHIPS_ON_DIGIT, 6, "😊"),
    JokerDef("mime", "Mime", "+3 Chips flat", JokerEffect.CHIPS_FLAT, 3, "🎭"),
    JokerDef("the_duo", "The Duo", "+1 Mult on word finish", JokerEffect.MULT_ON_WORD_COMPLETE, 1, "👥"),
]

MAX_JOKERS = 5


@dataclass
class JokerRuntime:
    definition: JokerDef
    bonus_chips: int = 0
    bonus_mult: float = 0.0


@dataclass
class JokerContext:
    """Context passed to joker effect calculations."""

    stats: StatsTracker
    streak: int
    last_word_perfect: bool
    last_word_length: int
    last_char_was_capital: bool
    last_char: str
    word_just_completed: bool


def apply_joker_effects(jokers: List[JokerDef], ctx: JokerContext) -> tuple[int, float]:
    """Return (bonus_chips, bonus_mult) from active jokers for current keystroke."""
    bonus_chips = 0
    bonus_mult = 0.0

    for joker in jokers:
        effect = joker.effect
        if effect == JokerEffect.FLAT_MULT:
            bonus_mult += joker.value
        elif effect == JokerEffect.CHIPS_PER_WORD:
            if ctx.word_just_completed:
                bonus_chips += int(joker.value)
        elif effect == JokerEffect.CHIPS_PER_STREAK:
            if ctx.streak > 0:
                bonus_chips += int(joker.value * min(ctx.streak, _STREAKER_STREAK_CAP))
        elif effect == JokerEffect.MULT_ON_PERFECT_WORD:
            if ctx.word_just_completed and ctx.last_word_perfect:
                bonus_chips += int(joker.value)
        elif effect == JokerEffect.CHIPS_LONG_WORD:
            if ctx.word_just_completed and ctx.last_word_length >= 5:
                bonus_chips += int(joker.value)
        elif effect == JokerEffect.CHIPS_CAPITAL:
            if ctx.last_char_was_capital:
                bonus_chips += int(joker.value)
        elif effect == JokerEffect.CHIPS_FLAT:
            bonus_chips += int(joker.value)
        elif effect == JokerEffect.MULT_ACCURACY:
            bonus_mult += joker.value * (ctx.stats.accuracy // 10)
        elif effect == JokerEffect.CHIPS_SHORT_WORD:
            if ctx.word_just_completed and 1 <= ctx.last_word_length <= 3:
                bonus_chips += int(joker.value)
        elif effect == JokerEffect.CHIPS_EXACT_WORD:
            if (
                ctx.word_just_completed
                and joker.word_length > 0
                and ctx.last_word_length == joker.word_length
            ):
                bonus_chips += int(joker.value)
        elif effect == JokerEffect.CHIPS_ON_PUNCTUATION:
            char = ctx.last_char
            if char and not char.isalnum() and not char.isspace():
                bonus_chips += int(joker.value)
        elif effect == JokerEffect.CHIPS_ON_DIGIT:
            if ctx.last_char.isdigit():
                bonus_chips += int(joker.value)
        elif effect == JokerEffect.MULT_ON_STREAK_TIER:
            if ctx.streak > 0:
                tiers = min(ctx.streak // _STREAK_TIER_SIZE, _STREAK_TIER_CAP)
                bonus_mult += joker.value * tiers
        elif effect == JokerEffect.MULT_ON_HIGH_ACCURACY:
            if ctx.stats.accuracy >= 90:
                bonus_mult += joker.value
        elif effect == JokerEffect.MULT_ON_WORD_COMPLETE:
            if ctx.word_just_completed:
                bonus_mult += joker.value
        else:
            raise ValueError(f"Unknown joker effect: {effect!r}")

    if bonus_chips > MAX_JOKER_CHIPS_PER_KEYSTROKE:
        bonus_chips = MAX_JOKER_CHIPS_PER_KEYSTROKE

    return bonus_chips, bonus_mult


def pick_random_jokers(count: int = 3, exclude: Optional[List[str]] = None) -> List[JokerDef]:
    """Pick random jokers for the reward screen."""
    exclude = exclude or []
    available = [j for j in JOKER_ROSTER if j.id not in exclude]
    return sample(available, min(count, len(available)))


def get_joker_by_id(joker_id: str) -> Optional[JokerDef]:
    for joker in JOKER_ROSTER:
        if joker.id == joker_id:
            return joker
    return None


def jokers_from_ids(ids: List[str]) -> List[JokerDef]:
    return [j for jid in ids if (j := get_joker_by_id(jid))]
