from typer.testing import CliRunner

from dev_workbench.cli import app


def test_doctor_reports_ok(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "status: ok" in result.output
    assert "command execution: approval required" in result.output
