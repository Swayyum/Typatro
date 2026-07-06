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

## Local development setup

Clone the repo and set up a local environment:

```bash
git clone https://github.com/Swayyum/Typatro.git
cd Typatro
uv sync --all-groups
source .venv/bin/activate
pre-commit install
typatro          # or: python -m typatro
```

If you see the typing screen, the install succeeded.

If `typatro` fails with `No module named 'typatro'`, recreate the venv:

```bash
rm -rf .venv && uv sync --all-groups && source .venv/bin/activate
```

Homebrew Python blocks global `pip install`; a venv avoids that and keeps `typatro` on your PATH while activated.

## Running tests

```bash
uv sync --all-groups
uv run python -m pytest tests/
```

## Releasing to TestPyPI / production PyPI

Maintainers usually publish via GitHub Actions:

- **TestPyPI** — workflow [Publish to TestPyPI](.github/workflows/publish-testpypi.yml); trigger on release publish or manual *workflow_dispatch*
- **Production PyPI** — workflow [Publish to PyPI](.github/workflows/publish-pypi.yml); same triggers, uses the `pypi` environment

Manual TestPyPI upload (when needed):

```bash
uv sync --all-groups
uv run python -m build
uv run twine upload --repository testpypi dist/*
```

Install from TestPyPI to verify:

```bash
python3 -m venv /tmp/typatro-test
source /tmp/typatro-test/bin/activate
python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ typatro
typatro --help
```

Use `--extra-index-url https://pypi.org/simple/` so dependencies resolve from the main PyPI index.

## Before opening a PR

- [ ] Update `CHANGELOG.md`
- [ ] Format your code with ruff
- [ ] Docstrings match the rest of the codebase

## Questions

Open a [GitHub discussion](https://github.com/Swayyum/Typatro/discussions) or issue and we'll help from there.
