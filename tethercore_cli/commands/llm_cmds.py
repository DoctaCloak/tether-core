import typer
from typing_extensions import Annotated

app = typer.Typer(help="Test LLM routing and interactions.", no_args_is_help=True)

@app.command()
def query(
    prompt: Annotated[str, typer.Argument(help="The prompt to send to the LLM.")],
    model: Annotated[str, typer.Option(help="Specify a model to route to (e.g., 'ollama/mistral', 'openai/gpt-4'). Optional.")] = None,
):
    """
    Send a query through LiteLLM to an LLM and get a response.
    """
    typer.echo(f"Sending prompt to LLM: '{prompt}'")
    if model:
        typer.echo(f"Attempting to use model: {model}")
    else:
        typer.echo("Using default LiteLLM routing.")

    # TODO: Implement actual LiteLLM query logic
    typer.secho("LLM query logic not yet implemented.", fg=typer.colors.YELLOW)
    typer.echo("LLM Response: This is a placeholder response from the LLM.")

@app.command()
def models():
    """
    List available models configured through LiteLLM.
    """
    typer.echo("Listing available LLM models (via LiteLLM configuration):")
    # TODO: Implement logic to fetch and display available models from LiteLLM config
    typer.secho("LLM model listing logic not yet implemented.", fg=typer.colors.YELLOW)
    typer.echo("- ollama/mistral (local)")
    typer.echo("- ollama/phi-3 (local)")
    typer.echo("- openai/gpt-3.5-turbo (cloud, if configured)")


if __name__ == "__main__":
    app()
