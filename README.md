# TYPATRO

A slot-machine typing roguelike for your terminal. Type fast, build **Chips x Mult**, beat Blinds, collect Jokers, and climb Antes — all wrapped in a casino-felt TUI with slot-reel animations.

## Features

- **Slot machine feel** — reel-spin title intro, odometer score tally that rolls as you type, digit-spin result reveals
- **Balatro-inspired game panel** — left sidebar with your current Blind, live Round Score (Chips x Mult), and held Jokers
- **Chips x Mult scoring** — +1 chip per correct character, +10 per word, mult scales with accuracy and error-free streaks
- **Blinds** — Small, Big, and Boss Blinds with score targets; bosses impose debuffs (hidden mistakes, minimum speed, no backspace, forced accuracy)
- **Jokers** — beat a blind, pick 1 of 3; up to 5 held jokers modify your scoring
- **Ante loop** — Small -> Big -> Boss, then the next ante with higher targets; run state persists between sessions
- **Classic mode** — a plain typing test when you just want to practice

## Install

Requires Python 3.9+.

```bash
pip install typatro
```

To pin a specific version:

```bash
pip install typatro==1.0.7
```

Then run:

```bash
typatro
```

A [Nerd Font](https://www.nerdfonts.com/) improves the icons but isn't required.

## Play

```bash
typatro            # run mode (default)
typatro --classic  # plain typing test
```

## How a run works

1. The sidebar shows your current **Blind** and its score target
2. Type the paragraph — the **Round Score** odometer rolls up with every keystroke
3. Hit the target before the test ends to beat the blind
4. Pick a **Joker** and advance; bosses add debuffs and bigger targets
5. Lose a blind? Retry it. Want a fresh start? Settings -> Danger Zone -> Reset Run

### Controls

| Key | Action |
|-----|--------|
| Type | Start the test |
| Tab | Reset test |
| Esc | New paragraph |
| Ctrl+S | Settings |
| Ctrl+T | Themes |
| Ctrl+L | Languages |

Click **Run/Classic** in the strip above the typing area to switch modes.

Contributors: see [CONTRIBUTING.md](CONTRIBUTING.md) on GitHub.

## Credits & license

GPL-3.0. TYPATRO by [Swayyum](https://github.com/Swayyum).
