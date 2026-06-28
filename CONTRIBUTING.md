# Contributing to Typatro! ⌨️

Thanks for taking the time to contribute to Typatro.

## What can I contribute?

- Add a theme
- Report a bug ([GitHub issue tracker](https://github.com/Swayyum/Typatro/issues))
- Suggest a new feature or enhancement ([GitHub issue tracker](https://github.com/Swayyum/Typatro/issues))
- Open a PR for any of the reasons above

<hr>

## Adding a theme

Theme files use Textual CSS (`.tcss`). Look at [existing themes](typatro/ui/css/themes) for examples.

Steps:

- Create a new theme file with a `.tcss` extension
- Place it in `typatro/ui/css/themes` (Typatro detects new themes automatically)
- Run the app and select the theme (see setup below)
- Make sure everything looks as expected

## Setting up a local environment

```bash
git clone https://github.com/Swayyum/Typatro.git
cd Typatro
uv sync --all-groups
source .venv/bin/activate
pre-commit install
typatro
```

If you see the typing screen, the install succeeded.

## Before opening a PR

- [ ] Update `CHANGELOG.md`
- [ ] Format your code with ruff
- [ ] Docstrings match the rest of the codebase

## Questions

Open a [GitHub discussion](https://github.com/Swayyum/Typatro/discussions) or issue and we'll help from there.
