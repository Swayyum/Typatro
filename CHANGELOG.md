# Changelog

All notable changes to this project will be documented in this file.



## 1.1.0

### Added

- **Boss blinds:** 10 boss blinds in rotation (5 new: The Ox, The Manacle, The Water, The Window, The Goad), each with distinct debuff behavior
- **Jokers:** 26 jokers in the roster (13 new), including new `JokerEffect` types for exact/short word chips, punctuation and digit bonuses, streak-tier mult, high-accuracy mult, and mult on word completion
- Joker card art mappings for expanded roster

## 1.0.8

### Changed

- GPL-3.0 LICENSE copyright notice and `license-files` metadata for PyPI

## 1.0.7

### Changed

- Move contributor and maintainer documentation out of the PyPI README into CONTRIBUTING.md; README stays end-user only

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 1.0.6

### Changed

- README install/docs cleanup for PyPI users: production install first, dev and maintainer sections separated


## 1.0.5

### Added

- Terminal-native cached shader backdrop (plasma-metaball frames) for the Balatro dither widget

### Changed

- Dither animation uses TerminalShader with performance-preserving typing pause

## 1.0.4

### Changed

- Fix typing lag in long sessions: pause header logo animation while typing, incremental stats counters
- Ticker updates less often and skips redraws when the value is unchanged
- Sidebar joker list shows numbered two-line cards with full name and effect (readable on dark themes)

## 1.0.3

### Changed

- Further typing/cursor performance: coalesced Rich spans, cached theme styles, lean render path
- Score sidebar no longer repaints on every keystroke (`push_score` hot path)
- Widget references cached after mount; dither pause avoids redundant timer work

## 1.0.2

### Changed

- Typing performance optimizations for Windows and smoother gliding during input
- Incremental span styling in the typing widget; layout refresh throttled during keystrokes
- Score panel: single odometer tick per keystroke with throttled roll refresh
- Dither animation slowed and paused while typing; ticker interval set to 0.2s

## 1.0.1

### Changed

- Veridia uses the standard swirling dither backdrop (no photo background)
- PyPI packaging: console script entry point, editable-install fix for Python 3.12+, TestPyPI release docs
- Removed legacy upstream references from docs and in-app copy

## 1.0.0

### Added

- TYPATRO — slot-machine typing roguelike with Blinds, Jokers, and Ante progression
- Vegas-style rainbow logo reel animation
- Chips × Mult scoring with odometer tally and digit-spin result reveals
- Run mode and classic mode
- PyPI packaging as `typatro` with setuptools build
- Reset Run clears boss debuffs and refreshes the sidebar UI
- Large `.tcss` theme library and custom theme support

### Changed

- Python 3.9 compatibility (replaced `match`/`case` with `if`/`elif`)
- Centered joker pick screen and improved header logo layout
