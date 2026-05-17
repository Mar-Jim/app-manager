from typer.testing import CliRunner

from dev_workbench.cli import app


def test_doctor_reports_ok(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "status: ok" in result.output
    assert "command execution: approval required" in result.output


def test_commands_suggest_lists_bundle_commands(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "databricks.yml").write_text("targets:\n  dev: {}\n", encoding="utf-8")

    result = CliRunner().invoke(app, ["commands", "suggest"])

    assert result.exit_code == 0
    assert "validate-bundle: databricks bundle validate -t dev [risk=low" in result.output
    assert "deploy-dev: databricks bundle deploy -t dev [risk=medium" in result.output


def test_commands_run_medium_without_yes_fails(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "databricks.yml").write_text("targets:\n  dev: {}\n", encoding="utf-8")

    result = CliRunner().invoke(app, ["commands", "run", "deploy-dev"])

    assert result.exit_code == 2
    assert "require explicit --yes" in result.output


def test_create_bundle_job_command_creates_project(tmp_path):
    result = CliRunner().invoke(app, ["create", "bundle-job", "demo-job", "--output-dir", str(tmp_path)])

    assert result.exit_code == 0
    assert "created:" in result.output
    assert (tmp_path / "demo-job/databricks.yml").exists()
    assert (tmp_path / "demo-job/resources/job.yml").exists()


def test_create_bundle_command_blocks_conflicts(tmp_path):
    runner = CliRunner()
    first = runner.invoke(app, ["create", "bundle-sql", "demo-sql", "--output-dir", str(tmp_path)])
    second = runner.invoke(app, ["create", "bundle-sql", "demo-sql", "--output-dir", str(tmp_path)])

    assert first.exit_code == 0
    assert second.exit_code == 2
    assert "files already exist" in second.output


def test_prompt_create_outputs_codex_prompt(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "databricks.yml").write_text("targets:\n  dev: {}\n", encoding="utf-8")

    result = CliRunner().invoke(app, ["prompt", "create", "--task-type", "add-workflow", "--task", "Add prompts."])

    assert result.exit_code == 0
    assert "## Goal" in result.output
    assert "Specific request: Add prompts." in result.output
    assert "Do not add stg/prd targets unless explicitly requested." in result.output


def test_handoff_create_and_show(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    created = CliRunner().invoke(app, ["handoff", "create", "--task", "Keep context lean."])
    shown = CliRunner().invoke(app, ["handoff", "show"])

    assert created.exit_code == 0
    assert shown.exit_code == 0
    assert "## Current State" in shown.output
    assert "Keep context lean." in shown.output
