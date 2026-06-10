# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 1.0.0

### Added

- TYPATRO — slot-machine typing roguelike with Blinds, Jokers, and Ante progression
- Vegas-style rainbow logo reel animation (slotslop-inspired)
- Chips × Mult scoring with odometer tally and digit-spin result reveals
- Run mode and classic mode
- PyPI packaging as `typatro` with setuptools build
- Reset Run clears boss debuffs and refreshes the sidebar UI

### Changed

- Renamed and rebranded from the upstream typing engine to **Typatro**
- Python 3.9 compatibility (replaced `match`/`case` with `if`/`elif`)
- Centered joker pick screen and improved header logo layout

## 0.x (upstream typing engine history)

Earlier releases shipped under other project names before the Typatro fork.
Cache and config paths now use the `typatro` app id:

```bash
python -c "import platformdirs; print(platformdirs.user_cache_dir('typatro'))"
```

### Added (historical)

- Ability to add custom themes
- More Everforest themes
- Header auto resize for large font sizes
- Cool setting section separators
- Strip in settings to jump to a specific section
- `Reset Config` option in settings
- Language packs stored in the user's local data dir
- Support for multiple languages and themes
- `TokyoNight` and Everforest Dark themes

### Fixed (historical)

- Inaccurate accuracy calculation after incorrect letters were fixed
- ZeroDivisionError in stats
- Indication for incorrect space
- Crash for Python build as root user
- Bug when creating/saving a new user config
- Double keypress on typing screen
- Keypress not working after resetting config
- Blind mode not working
- App crash when cursor buddy finishes the test before you
- Delay for restrictions because the initial calculation is highly variable
- Permanent blind mode fix
- `--version` crash for binary formats
- `ctrl+w` on the first letter crashing the app
- Clicking a setting option not changing the setting
- Backspace color rendering issues
- Language pack addition not working for binaries

### Removed (historical)

- Mechanical sounds (planned for a future release)
