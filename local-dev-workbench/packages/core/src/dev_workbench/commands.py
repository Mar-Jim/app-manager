from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from pathlib import Path

from dev_workbench.detect import detect_project
from dev_workbench.models import CommandRunResult, GeneratedCommand, RiskLevel


RISK_CONFIRMATION_LEVELS = {"medium", "high", "destructive"}
DESTRUCTIVE_TERMS = ("delete", "drop", "remove", "rm")


class CommandExecutionError(ValueError):
    pass


def suggest_commands(root: Path | None = None) -> list[GeneratedCommand]:
    base = (root or Path.cwd()).resolve()
    detection = detect_project(base)

    if detection.project.project_type != "databricks_asset_bundle":
        return []

    return [
        _build_command(
            command_id="validate-bundle",
            label="Validate Bundle",
            argv=["databricks", "bundle", "validate", "-t", "dev"],
            working_dir=base,
            reason="Validate the Databricks Asset Bundle against the dev target before making changes.",
        ),
        _build_command(
            command_id="run-tests",
            label="Run Tests",
            argv=["pytest"],
            working_dir=base,
            reason="Run the local Python test suite for the current project.",
        ),
        _build_command(
            command_id="deploy-dev",
            label="Deploy Dev",
            argv=["databricks", "bundle", "deploy", "-t", "dev"],
            working_dir=base,
            reason="Deploy the Databricks Asset Bundle to the dev target.",
        ),
        _build_command(
            command_id="bundle-summary",
            label="Bundle Summary",
            argv=["databricks", "bundle", "validate", "-t", "dev", "--output", "json"],
            working_dir=base,
            reason="Generate a machine-readable bundle validation summary when the installed CLI supports JSON output.",
        ),
    ]


def list_generated_commands(root: Path | None = None) -> list[GeneratedCommand]:
    return suggest_commands(root)


def classify_risk(argv: list[str]) -> RiskLevel:
    normalized = [part.lower() for part in argv]

    if any(part.lstrip("-") in DESTRUCTIVE_TERMS for part in normalized):
        return "destructive"

    if normalized == ["pytest"]:
        return "low"

    if normalized[:3] == ["databricks", "bundle", "validate"]:
        return "low"

    if normalized[:3] == ["databricks", "bundle", "deploy"] and "-t" in normalized:
        target_index = normalized.index("-t") + 1
        if target_index < len(normalized) and normalized[target_index] == "dev":
            return "medium"

    if normalized[:2] == ["git", "push"]:
        return "high"

    return "medium"


def run_command(command_id: str, *, yes: bool = False, root: Path | None = None) -> CommandRunResult:
    command = _find_command(command_id, root)

    if command.risk_level == "destructive":
        raise CommandExecutionError("Destructive commands are not supported yet.")

    if command.risk_level in RISK_CONFIRMATION_LEVELS and not yes:
        raise CommandExecutionError(f"{command.risk_level} risk commands require explicit --yes confirmation.")

    argv = [command.command, *command.args]
    started_at = _now()
    completed = subprocess.run(
        argv,
        cwd=command.working_dir,
        capture_output=True,
        text=True,
        shell=False,
        check=False,
    )
    ended_at = _now()

    return CommandRunResult(
        command_id=command.id,
        status="succeeded" if completed.returncode == 0 else "failed",
        stdout=completed.stdout,
        stderr=completed.stderr,
        exit_code=completed.returncode,
        started_at=started_at,
        ended_at=ended_at,
    )


def _find_command(command_id: str, root: Path | None) -> GeneratedCommand:
    for command in suggest_commands(root):
        if command.id == command_id:
            return command
    raise CommandExecutionError(f"Unknown generated command id: {command_id}")


def _build_command(
    *,
    command_id: str,
    label: str,
    argv: list[str],
    working_dir: Path,
    reason: str,
) -> GeneratedCommand:
    risk_level = classify_risk(argv)
    return GeneratedCommand(
        id=command_id,
        label=label,
        command=argv[0],
        args=argv[1:],
        working_dir=str(working_dir),
        risk_level=risk_level,
        reason=reason,
        requires_confirmation=risk_level in RISK_CONFIRMATION_LEVELS,
    )


def _now() -> str:
    return datetime.now(UTC).isoformat()
