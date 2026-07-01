# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
