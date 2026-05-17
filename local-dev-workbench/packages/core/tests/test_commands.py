import subprocess

import pytest

from dev_workbench.commands import CommandExecutionError, classify_risk, run_command, suggest_commands
from dev_workbench.models import GeneratedCommand


def test_command_suggestions_for_bundle_repo(tmp_path):
    (tmp_path / "databricks.yml").write_text(
        "bundle:\n"
        "  name: demo\n"
        "targets:\n"
        "  dev: {}\n",
        encoding="utf-8",
    )

    commands = suggest_commands(tmp_path)

    assert [command.id for command in commands] == [
        "validate-bundle",
        "run-tests",
        "deploy-dev",
        "bundle-summary",
    ]
    assert commands[0].command == "databricks"
    assert commands[0].args == ["bundle", "validate", "-t", "dev"]
    assert commands[0].risk_level == "low"
    assert commands[2].risk_level == "medium"
    assert commands[2].requires_confirmation is True
    assert commands[3].args == ["bundle", "validate", "-t", "dev", "--output", "json"]


def test_risk_classification():
    assert classify_risk(["pytest"]) == "low"
    assert classify_risk(["databricks", "bundle", "validate", "-t", "dev"]) == "low"
    assert classify_risk(["databricks", "bundle", "deploy", "-t", "dev"]) == "medium"
    assert classify_risk(["git", "push"]) == "high"
    assert classify_risk(["databricks", "bundle", "destroy", "--delete"]) == "destructive"


def test_subprocess_runner_uses_argument_array(tmp_path, monkeypatch):
    (tmp_path / "databricks.yml").write_text("targets:\n  dev: {}\n", encoding="utf-8")
    calls = []

    def fake_run(argv, **kwargs):
        calls.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 0, stdout="ok\n", stderr="")

    monkeypatch.setattr("dev_workbench.commands.subprocess.run", fake_run)

    result = run_command("validate-bundle", root=tmp_path)

    assert result.status == "succeeded"
    assert result.stdout == "ok\n"
    assert calls == [
        (
            ["databricks", "bundle", "validate", "-t", "dev"],
            {
                "cwd": str(tmp_path.resolve()),
                "capture_output": True,
                "text": True,
                "shell": False,
                "check": False,
            },
        )
    ]


def test_medium_commands_require_confirmation(tmp_path):
    (tmp_path / "databricks.yml").write_text("targets:\n  dev: {}\n", encoding="utf-8")

    with pytest.raises(CommandExecutionError, match="require explicit --yes"):
        run_command("deploy-dev", root=tmp_path)


def test_destructive_commands_are_blocked(monkeypatch, tmp_path):
    destructive = GeneratedCommand(
        id="drop-table",
        label="Drop Table",
        command="databricks",
        args=["tables", "delete", "demo"],
        working_dir=str(tmp_path),
        risk_level="destructive",
        reason="Delete a table.",
        requires_confirmation=True,
    )

    monkeypatch.setattr("dev_workbench.commands.suggest_commands", lambda root=None: [destructive])

    with pytest.raises(CommandExecutionError, match="Destructive commands are not supported"):
        run_command("drop-table", yes=True, root=tmp_path)
