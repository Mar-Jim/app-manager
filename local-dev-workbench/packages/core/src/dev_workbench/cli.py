from pathlib import Path

import typer
import uvicorn

from dev_workbench import __version__
from dev_workbench.commands import list_generated_commands
from dev_workbench.detect import detect_project
from dev_workbench.storage import initialize_database

app = typer.Typer(help="Local-first developer workbench.")
handoff_app = typer.Typer(help="Create and manage handoff files.")
commands_app = typer.Typer(help="List generated commands for approval.")
app.add_typer(handoff_app, name="handoff")
app.add_typer(commands_app, name="commands")


@app.command()
def doctor() -> None:
    """Check that the local workbench can start."""
    db_path = initialize_database()
    typer.echo(f"local-dev-workbench {__version__}")
    typer.echo("status: ok")
    typer.echo(f"sqlite: {db_path}")
    typer.echo("command execution: approval required")


@app.command()
def detect() -> None:
    """Detect known local project markers in the current directory."""
    result = detect_project()
    typer.echo(result.model_dump_json(indent=2))


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="Local bind address."),
    port: int = typer.Option(8787, help="Local API port."),
) -> None:
    """Run the local FastAPI backend."""
    uvicorn.run("dev_workbench.api.app:app", host=host, port=port, reload=True)


@handoff_app.command("create")
def handoff_create(path: Path = typer.Option(Path("handoff/current.md"), help="Handoff file to create.")) -> None:
    """Create a local handoff file if it does not already exist."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(
            "# Current Handoff\n\n"
            "## State\n"
            "- Initial handoff created by `workbench handoff create`.\n\n"
            "## Next Recommended Prompt\n"
            "Continue building local-dev-workbench from the current handoff.\n",
            encoding="utf-8",
        )
    typer.echo(f"handoff: {path}")


@commands_app.command("list")
def commands_list() -> None:
    """List generated commands without executing them."""
    for command in list_generated_commands():
        command_text = " ".join(command.command)
        typer.echo(f"{command.id}: {command_text} [approval_required={command.requires_approval}]")
