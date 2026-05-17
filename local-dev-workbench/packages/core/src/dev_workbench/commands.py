from dev_workbench.models import GeneratedCommand


def list_generated_commands() -> list[GeneratedCommand]:
    return [
        GeneratedCommand(
            id="validate-bundle",
            label="Validate Bundle",
            command=["databricks", "bundle", "validate"],
            risk="reads local bundle configuration and validates against Databricks CLI behavior",
        ),
        GeneratedCommand(
            id="run-tests",
            label="Run Tests",
            command=["pytest"],
            risk="runs local tests only",
        ),
        GeneratedCommand(
            id="create-codex-prompt",
            label="Create Codex Prompt",
            command=["workbench", "handoff", "create"],
            risk="creates or updates local handoff content",
        ),
    ]
