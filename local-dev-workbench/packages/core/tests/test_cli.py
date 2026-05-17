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


def test_todo_cli_add_list_complete(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    added = runner.invoke(app, ["todo", "add", "Write local todos"])
    listed = runner.invoke(app, ["todo", "list"])
    completed = runner.invoke(app, ["todo", "complete", "1"])
    listed_again = runner.invoke(app, ["todo", "list"])

    assert added.exit_code == 0
    assert "1: Write local todos" in added.output
    assert listed.exit_code == 0
    assert "1. [ ] Write local todos" in listed.output
    assert completed.exit_code == 0
    assert "completed: 1: Write local todos" in completed.output
    assert "1. [x] Write local todos" in listed_again.output


def test_worklog_cli_add_and_summary(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    added = runner.invoke(app, ["worklog", "add", "Finished CLI support"])
    summary = runner.invoke(app, ["worklog", "summary"])

    assert added.exit_code == 0
    assert "1: Finished CLI support" in added.output
    assert summary.exit_code == 0
    assert "Today I worked on:\n- Finished CLI support" in summary.output
    assert "Completed:\n- None" in summary.output


def test_ado_cli_no_token_guidance(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("WORKBENCH_ADO_ORGANIZATION_URL", "https://dev.azure.com/example")
    monkeypatch.setenv("WORKBENCH_ADO_PROJECT", "Demo")
    monkeypatch.setenv("WORKBENCH_ADO_PAT_ENV_VAR", "MISSING_ADO_PAT")
    monkeypatch.delenv("MISSING_ADO_PAT", raising=False)

    result = CliRunner().invoke(app, ["ado", "tickets", "list"])

    assert result.exit_code == 0
    assert "MISSING_ADO_PAT" in result.output
    assert "No Azure DevOps tickets available." in result.output


def test_ado_cli_draft_update_is_local_without_token(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["ado", "ticket", "draft-update", "42", "--note", "Validated locally."])

    assert result.exit_code == 0
    assert "draft: 1" in result.output
    assert "Update for #42: Azure DevOps #42" in result.output
    assert "- Validated locally." in result.output


def test_ado_cli_post_requires_yes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(app, ["ado", "ticket", "draft-update", "42", "--note", "Validated locally."])

    result = runner.invoke(app, ["ado", "ticket", "post-update", "42", "--from-draft"])

    assert result.exit_code == 2
    assert "requires explicit --yes" in result.output
