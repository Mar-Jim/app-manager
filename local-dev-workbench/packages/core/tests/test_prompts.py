from dev_workbench.prompts import create_handoff, generate_prompt


def test_prompt_generation_for_add_workflow_includes_required_sections(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname = \"demo\"\n", encoding="utf-8")

    result = generate_prompt(
        task_type="add-workflow",
        task_description="Add a command history page.",
        root=tmp_path,
    )

    assert result.task_type == "add-workflow"
    assert "## Goal" in result.prompt
    assert "Specific request: Add a command history page." in result.prompt
    assert "## Current repo context" in result.prompt
    assert "## Handoff update requirement" in result.prompt
    assert "- Type: python_project" in result.prompt


def test_databricks_external_deployer_constraints_appear_in_prompt(tmp_path):
    (tmp_path / "databricks.yml").write_text("targets:\n  dev: {}\n", encoding="utf-8")

    result = generate_prompt(task_type="fix-bundle-error", root=tmp_path)

    assert "This repo usually defines only dev target." in result.prompt
    assert "stg/prd are handled by external deployer repo." in result.prompt
    assert "Do not add stg/prd targets unless explicitly requested." in result.prompt
    assert "Prefer local-first commands." in result.prompt
    assert "Ask before execution." in result.prompt
    assert "- `databricks bundle validate -t dev`" in result.prompt


def test_prompt_output_is_deterministic_enough_for_text_assertions(tmp_path):
    (tmp_path / "databricks.yml").write_text("targets:\n  dev: {}\n", encoding="utf-8")

    first = generate_prompt(task_type="write-tests", task_description="Cover prompt snapshots.", root=tmp_path)
    second = generate_prompt(task_type="write-tests", task_description="Cover prompt snapshots.", root=tmp_path)

    assert first.prompt == second.prompt


def test_handoff_file_creation_uses_required_format(tmp_path):
    path, content = create_handoff(
        task_type="add-workflow",
        task_description="Add prompt generation.",
        root=tmp_path,
    )

    assert path == tmp_path / "handoff/current.md"
    assert path.exists()
    assert path.read_text(encoding="utf-8") == content
    for section in [
        "Goal",
        "Current State",
        "Architecture Decisions",
        "Files Changed",
        "Commands Run",
        "Test Results",
        "Open Issues",
        "Next Recommended Codex Prompt",
        "Constraints",
        "Do Not Change",
    ]:
        assert f"## {section}" in content
