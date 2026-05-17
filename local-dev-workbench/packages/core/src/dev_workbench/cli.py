from pathlib import Path

import typer
import uvicorn

from dev_workbench import __version__
from dev_workbench.commands import CommandExecutionError, run_command, suggest_commands
from dev_workbench.detect import detect_project
from dev_workbench.storage import initialize_database

app = typer.Typer(help="Local-first developer workbench.")
handoff_app = typer.Typer(help="Create and manage handoff files.")
commands_app = typer.Typer(help="Suggest and run generated commands after approval.")
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
def detect(json_output: bool = typer.Option(False, "--json", help="Output detection result as JSON.")) -> None:
    """Detect the local project type in the current directory."""
    result = detect_project()
    if json_output:
        typer.echo(result.model_dump_json(indent=2))
        return

    typer.echo("Project detection")
    typer.echo(f"type: {result.project.project_type}")
    typer.echo(f"root: {result.project.root_path}")
    detected_files = ", ".join(result.project.detected_files) if result.project.detected_files else "none"
    typer.echo(f"detected files: {detected_files}")
    if result.databricks_bundle:
        targets = ", ".join(result.databricks_bundle.targets) if result.databricks_bundle.targets else "none"
        typer.echo(f"bundle file: {result.databricks_bundle.bundle_file}")
        typer.echo(f"databricks targets: {targets}")
        typer.echo(f"only dev target: {result.databricks_bundle.only_dev_target}")
        typer.echo(f"deployment strategy: {result.databricks_bundle.deployment_strategy}")
    typer.echo(f"message: {result.message}")


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
    _print_suggested_commands()


@commands_app.command("suggest")
def commands_suggest() -> None:
    """Suggest generated commands without executing them."""
    _print_suggested_commands()


@commands_app.command("run")
def commands_run(
    command_id: str = typer.Argument(..., metavar="COMMAND_ID"),
    yes: bool = typer.Option(False, "--yes", help="Confirm medium, high, or destructive risk commands."),
) -> None:
    """Run a generated command by id."""
    try:
        result = run_command(command_id, yes=yes)
    except CommandExecutionError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(f"status: {result.status}")
    typer.echo(f"exit_code: {result.exit_code}")
    if result.stdout:
        typer.echo("stdout:")
        typer.echo(result.stdout)
    if result.stderr:
        typer.echo("stderr:")
        typer.echo(result.stderr)


def _print_suggested_commands() -> None:
    commands = suggest_commands()
    if not commands:
        typer.echo("No generated commands available for this project.")
        return

    for command in commands:
        command_text = " ".join([command.command, *command.args])
        typer.echo(
            f"{command.id}: {command_text} "
            f"[risk={command.risk_level}, confirmation_required={command.requires_confirmation}]"
        )
