# Contributing to Typatro! ⌨️

Thanks for taking the time to contribute to Typatro.

## What can I contribute?

You can do that in a lot of ways

- Add a theme
- Report a bug ( [see GitHub issue tracker](https://github.com/Swayyum/Typatro/issues) )
- Suggest a new feature or enhancement ( [see GitHub issue tracker](https://github.com/Swayyum/Typatro/issues) )
- Open a PR for any of the reasons above

<hr>


## Adding a theme

Currently, we're using [themes from monkeytype](https://github.com/monkeytypegame/monkeytype/tree/master/frontend/static/themes) but if you feel like some theme is missing, 
feel free to open a PR to add it! \

The theme format is pretty simple and you can look into [any of the theme files](typatro/ui/css/themes)

Steps:

- Create a new theme file with `.tcss` extension
- Place it inside dir `typatro/ui/css/themes` (typatro will automatically detect the new theme)
- Run the app (see setup) and select the theme ( [see setup](#setting-up-local-environment) )
- make sure everything looks as expected

## Setting up Local environment

Steps:
- Fork and Clone the repo to your local machine
  
- run `pip install -e .` \
  This will install typatro and all required dependencies in your environment

- run `pre-commit install` \
  This will set pre-commit hooks for GitHub which will automatically run `ruff` to test your code

- Finally, you can run the app
  ```bash
  typatro
  ```

- If you see a typing screen that means everything is installed properly


## Before opening a PR

Before you open your PR, please go through this checklist and make sure you've checked all the items that apply:

 - [ ] Update the `CHANGELOG.md`
 - [ ] Format your code with ruff
 - [ ] All your code has docstrings in the style of the rest of the codebase

## Questions
If you have any questions, comments, concerns, or problems let me know on [Discord](https://discord.com/invite/WA2ER9MBWa) or ask a question on Typatro's GitHub discussions and I'll be happy to assist you.
