import click

PKG_VERSION = "1.0.0"


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=True,
)
@click.option(
    "--version",
    "-v",
    is_flag=True,
    help="Show version and exit.",
)
@click.option(
    "--classic",
    is_flag=True,
    help="Run in classic mode (no Balatro run mechanics).",
)
@click.pass_context
def main(ctx, version: bool, classic: bool) -> None:
    if version:
        return print(f"typatro - v{PKG_VERSION}")

    if ctx.invoked_subcommand is None:
        from typatro.src import config_parser
        from typatro.ui.tui import Typatro

        if classic:
            config_parser.set("game_mode", "classic")
        else:
            config_parser.set("game_mode", "run")

        from typatro.src.background_music import stop_background_music

        app = Typatro()
        try:
            app.run()
        finally:
            stop_background_music()


@main.command(help="Add a language to typatro")
@click.argument("name")
def add(name: str) -> None:
    from typatro.src.plugins.add_language import AddLanguage

    AddLanguage().add(name)


if __name__ == "__main__":
    main()
