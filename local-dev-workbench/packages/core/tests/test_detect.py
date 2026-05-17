import json

from typer.testing import CliRunner

from dev_workbench.cli import app
from dev_workbench.detect import detect_project


def test_unknown_folder(tmp_path):
    result = detect_project(tmp_path)

    assert result.project.project_type == "unknown"
    assert result.project.detected_files == []
    assert result.databricks_bundle is None


def test_databricks_bundle_with_only_dev_target(tmp_path):
    (tmp_path / "databricks.yml").write_text(
        "bundle:\n"
        "  name: demo\n"
        "targets:\n"
        "  dev:\n"
        "    default: true\n",
        encoding="utf-8",
    )

    result = detect_project(tmp_path)

    assert result.project.project_type == "databricks_asset_bundle"
    assert result.databricks_bundle is not None
    assert result.databricks_bundle.targets == ["dev"]
    assert result.databricks_bundle.only_dev_target is True
    assert result.databricks_bundle.deployment_strategy == "local_dev_external_deployer_candidate"


def test_databricks_bundle_with_dev_stg_prd_targets(tmp_path):
    (tmp_path / "databricks.yaml").write_text(
        "targets:\n"
        "  prd: {}\n"
        "  dev: {}\n"
        "  stg: {}\n",
        encoding="utf-8",
    )

    result = detect_project(tmp_path)

    assert result.project.project_type == "databricks_asset_bundle"
    assert result.databricks_bundle is not None
    assert result.databricks_bundle.targets == ["dev", "stg", "prd"]
    assert result.databricks_bundle.only_dev_target is False
    assert result.databricks_bundle.deployment_strategy == "local_multi_target"


def test_python_project(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")

    result = detect_project(tmp_path)

    assert result.project.project_type == "python_project"
    assert result.project.detected_files == ["pyproject.toml"]


def test_node_project(tmp_path):
    (tmp_path / "package.json").write_text('{"name":"demo"}\n', encoding="utf-8")

    result = detect_project(tmp_path)

    assert result.project.project_type == "node_project"
    assert result.project.detected_files == ["package.json"]


def test_databricks_app_project(tmp_path):
    (tmp_path / "app.yaml").write_text("name: demo\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("print('hello')\n", encoding="utf-8")

    result = detect_project(tmp_path)

    assert result.project.project_type == "databricks_app"
    assert result.project.detected_files == ["app.yaml", "app.py"]


def test_vscode_extension_project(tmp_path):
    (tmp_path / "package.json").write_text(
        '{"name":"demo","engines":{"vscode":"^1.90.0"},"contributes":{}}\n',
        encoding="utf-8",
    )

    result = detect_project(tmp_path)

    assert result.project.project_type == "vscode_extension"


def test_detect_cli_outputs_pretty_text_by_default(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")

    result = CliRunner().invoke(app, ["detect"])

    assert result.exit_code == 0
    assert "Project detection" in result.output
    assert "type: python_project" in result.output


def test_detect_cli_outputs_json(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["detect", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["project"]["project_type"] == "unknown"
