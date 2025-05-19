import typer
from typing_extensions import Annotated

# Import command groups
from .commands import echo_cmds
from .commands import chain_cmds
from .commands import agent_cmds
from .commands import llm_cmds
from .commands import config_cmds

# Create the main Typer application instance
app = typer.Typer(
    name="tether-cli",
    help="TetherCore: A Sovereign AI Companion - Command Line Interface.",
    add_completion=False, # Disable shell completion for now, can be enabled later
    no_args_is_help=True   # Show help if no command is given
)

# Add subcommands (routers) from the command modules
app.add_typer(echo_cmds.app, name="echo", help="Manage Echos (memories, thoughts, goals).")
app.add_typer(chain_cmds.app, name="chain", help="Interact with TetherChain (memory log).")
app.add_typer(agent_cmds.app, name="agent", help="Manage Mindscape Agents.")
app.add_typer(llm_cmds.app, name="llm", help="Test LLM routing and interactions.")
app.add_typer(config_cmds.app, name="config", help="Manage TetherCore configuration.")


@app.callback()
def main_callback(
    ctx: typer.Context,
    # Example of a global option, e.g., for a config file path
    # config_file: Annotated[
    #     Optional[Path],
    #     typer.Option(
    #         "--config",
    #         help="Path to the TetherCore configuration file.",
    #         envvar="TETHER_CONFIG_PATH",
    #         resolve_path=True,
    #     ),
    # ] = None,
    version: Annotated[
        bool,
        typer.Option("--version", "-v", help="Show the application version and exit."),
    ] = False,
):
    """
    TetherCore CLI main entry point.
    """
    if version:
        from . import __version__ # Import from the package __init__
        typer.echo(f"tether-cli version: {__version__}")
        raise typer.Exit()

    # You can load configuration or initialize services here if needed globally
    # For example:
    # if config_file:
    #     typer.echo(f"Using config file: {config_file}")
    #     # Load config logic
    # else:
    #     typer.echo("No config file specified. Using default settings.")
    #
    # ctx.obj = {"config_file": config_file, "some_service": SomeService()}


if __name__ == "__main__":
    app()
