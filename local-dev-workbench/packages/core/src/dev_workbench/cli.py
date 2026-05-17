from pathlib import Path

import typer
import uvicorn

from dev_workbench import __version__
from dev_workbench.commands import CommandExecutionError, run_command, suggest_commands
from dev_workbench.detect import detect_project
from dev_workbench.models import PromptTaskType
from dev_workbench.prompts import create_handoff as create_handoff_file
from dev_workbench.prompts import generate_prompt, save_prompt, show_handoff
from dev_workbench.projects import (
    DEFAULT_DEPLOYMENT_STRATEGY,
    DEFAULT_TARGET,
    ProjectCreateError,
    ProjectKind,
    create_project,
)
from dev_workbench.storage import initialize_database
from dev_workbench.work import WorkbenchService

app = typer.Typer(help="Local-first developer workbench.")
create_app = typer.Typer(help="Create starter local projects.")
handoff_app = typer.Typer(help="Create and manage handoff files.")
commands_app = typer.Typer(help="Suggest and run generated commands after approval.")
prompt_app = typer.Typer(help="Generate Codex prompts from local project context.")
todo_app = typer.Typer(help="Track local todos.")
worklog_app = typer.Typer(help="Track local daily work notes.")
app.add_typer(create_app, name="create")
app.add_typer(handoff_app, name="handoff")
app.add_typer(commands_app, name="commands")
app.add_typer(prompt_app, name="prompt")
app.add_typer(todo_app, name="todo")
app.add_typer(worklog_app, name="worklog")


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
def handoff_create(
    path: Path = typer.Option(Path("handoff/current.md"), help="Handoff file to create or update."),
    task_type: PromptTaskType = typer.Option("add-workflow", "--task-type", help="Prompt task type to seed the handoff."),
    task: str = typer.Option("", "--task", help="Task description for the next recommended prompt."),
) -> None:
    """Create or update a local handoff file."""
    output_path, _content = create_handoff_file(path=path, task_type=task_type, task_description=task)
    typer.echo(f"handoff: {output_path}")


@handoff_app.command("show")
def handoff_show(path: Path = typer.Option(Path("handoff/current.md"), help="Handoff file to display.")) -> None:
    """Show the current local handoff file."""
    try:
        _path, content = show_handoff(path=path)
    except FileNotFoundError as exc:
        typer.echo(f"error: handoff file not found: {path}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(content)


@prompt_app.command("create")
def prompt_create(
    task_type: PromptTaskType = typer.Option("add-workflow", "--task-type", help="Prompt task type."),
    task: str = typer.Option("", "--task", help="Task description to include in the generated prompt."),
    save: bool = typer.Option(False, "--save", help="Save the generated prompt under prompts/."),
    file_name: str | None = typer.Option(None, "--file-name", help="Optional prompt file name when saving."),
) -> None:
    """Generate a medium-sized Codex prompt from local project context."""
    if save:
        output_path, prompt = save_prompt(task_type=task_type, task_description=task, file_name=file_name)
        typer.echo(prompt)
        typer.echo(f"saved: {output_path}")
        return

    result = generate_prompt(task_type=task_type, task_description=task)
    typer.echo(result.prompt)


@todo_app.command("add")
def todo_add(text: str = typer.Argument(..., metavar="TEXT")) -> None:
    """Add a local todo."""
    todo = WorkbenchService().add_todo(text)
    typer.echo(f"{todo.id}: {todo.text}")


@todo_app.command("list")
def todo_list() -> None:
    """List local todos."""
    todos = WorkbenchService().list_todos()
    if not todos:
        typer.echo("No todos.")
        return
    for todo in todos:
        status = "x" if todo.completed else " "
        typer.echo(f"{todo.id}. [{status}] {todo.text}")


@todo_app.command("complete")
def todo_complete(todo_id: int = typer.Argument(..., metavar="ID")) -> None:
    """Mark a local todo complete."""
    try:
        todo = WorkbenchService().complete_todo(todo_id)
    except ValueError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(f"completed: {todo.id}: {todo.text}")


@worklog_app.command("add")
def worklog_add(text: str = typer.Argument(..., metavar="TEXT")) -> None:
    """Add a local work log entry."""
    entry = WorkbenchService().add_worklog(text)
    typer.echo(f"{entry.id}: {entry.text}")


@worklog_app.command("summary")
def worklog_summary() -> None:
    """Generate a local daily summary draft."""
    typer.echo(WorkbenchService().generate_daily_summary())


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


@create_app.command("bundle-job")
def create_bundle_job(
    name: str = typer.Argument(..., metavar="NAME"),
    output_dir: Path | None = typer.Option(None, "--output-dir", help="Directory that will receive the project folder."),
    force: bool = typer.Option(False, "--force", help="Overwrite existing generated files."),
    include_github_action: bool = typer.Option(
        False,
        "--include-github-action/--no-include-github-action",
        help="Include a GitHub Action workflow when supported.",
    ),
    deployment_strategy: str = typer.Option(DEFAULT_DEPLOYMENT_STRATEGY, "--deployment-strategy"),
    target: str = typer.Option(DEFAULT_TARGET, "--target"),
) -> None:
    """Create a starter Databricks Asset Bundle workflow job project."""
    _create_project_command(
        kind="bundle-job",
        name=name,
        output_dir=output_dir,
        force=force,
        include_github_action=include_github_action,
        deployment_strategy=deployment_strategy,
        target=target,
    )


@create_app.command("bundle-pipeline")
def create_bundle_pipeline(
    name: str = typer.Argument(..., metavar="NAME"),
    output_dir: Path | None = typer.Option(None, "--output-dir", help="Directory that will receive the project folder."),
    force: bool = typer.Option(False, "--force", help="Overwrite existing generated files."),
    include_github_action: bool = typer.Option(
        False,
        "--include-github-action/--no-include-github-action",
        help="Include a GitHub Action workflow when supported.",
    ),
    deployment_strategy: str = typer.Option(DEFAULT_DEPLOYMENT_STRATEGY, "--deployment-strategy"),
    target: str = typer.Option(DEFAULT_TARGET, "--target"),
) -> None:
    """Create a starter Databricks Asset Bundle DLT or Lakeflow pipeline project."""
    _create_project_command(
        kind="bundle-pipeline",
        name=name,
        output_dir=output_dir,
        force=force,
        include_github_action=include_github_action,
        deployment_strategy=deployment_strategy,
        target=target,
    )


@create_app.command("bundle-sql")
def create_bundle_sql(
    name: str = typer.Argument(..., metavar="NAME"),
    output_dir: Path | None = typer.Option(None, "--output-dir", help="Directory that will receive the project folder."),
    force: bool = typer.Option(False, "--force", help="Overwrite existing generated files."),
    include_github_action: bool = typer.Option(
        False,
        "--include-github-action/--no-include-github-action",
        help="Include a GitHub Action workflow when supported.",
    ),
    deployment_strategy: str = typer.Option(DEFAULT_DEPLOYMENT_STRATEGY, "--deployment-strategy"),
    target: str = typer.Option(DEFAULT_TARGET, "--target"),
) -> None:
    """Create a starter Databricks Asset Bundle SQL and tables project."""
    _create_project_command(
        kind="bundle-sql",
        name=name,
        output_dir=output_dir,
        force=force,
        include_github_action=include_github_action,
        deployment_strategy=deployment_strategy,
        target=target,
    )


@create_app.command("bundle-dashboard")
def create_bundle_dashboard(
    name: str = typer.Argument(..., metavar="NAME"),
    output_dir: Path | None = typer.Option(None, "--output-dir", help="Directory that will receive the project folder."),
    force: bool = typer.Option(False, "--force", help="Overwrite existing generated files."),
    include_github_action: bool = typer.Option(
        False,
        "--include-github-action/--no-include-github-action",
        help="Include a GitHub Action workflow when supported.",
    ),
    deployment_strategy: str = typer.Option(DEFAULT_DEPLOYMENT_STRATEGY, "--deployment-strategy"),
    target: str = typer.Option(DEFAULT_TARGET, "--target"),
) -> None:
    """Create a starter Databricks Asset Bundle dashboard skeleton."""
    _create_project_command(
        kind="bundle-dashboard",
        name=name,
        output_dir=output_dir,
        force=force,
        include_github_action=include_github_action,
        deployment_strategy=deployment_strategy,
        target=target,
    )


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


def _create_project_command(
    *,
    kind: ProjectKind,
    name: str,
    output_dir: Path | None,
    force: bool,
    include_github_action: bool,
    deployment_strategy: str,
    target: str,
) -> None:
    try:
        result = create_project(
            kind=kind,
            name=name,
            output_dir=output_dir,
            force=force,
            include_github_action=include_github_action,
            deployment_strategy=deployment_strategy,
            target=target,
        )
    except ProjectCreateError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    if result["conflicts"] and not force:
        typer.echo("error: files already exist; rerun with --force to overwrite.", err=True)
        for conflict in result["conflicts"]:
            typer.echo(f"conflict: {conflict}", err=True)
        raise typer.Exit(code=2)

    typer.echo(f"created: {result['root_path']}")
    for file_path in result["files"]:
        typer.echo(f"file: {file_path}")
