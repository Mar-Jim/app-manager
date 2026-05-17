from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from dev_workbench.commands import suggest_commands
from dev_workbench.detect import detect_project
from dev_workbench.models import DetectionResult, GeneratedPromptResult, PromptTaskType


PROMPT_SECTIONS = (
    "Goal",
    "Current repo context",
    "Constraints",
    "Company/security assumptions",
    "Databricks deployment strategy",
    "Task",
    "Expected files to change",
    "Validation commands",
    "Definition of done",
    "Handoff update requirement",
)

HANDOFF_SECTIONS = (
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
)

TASK_DEFAULTS: dict[PromptTaskType, dict[str, str]] = {
    "add-workflow": {
        "goal": "Add or refine a local-first workflow in this repository.",
        "task": "Implement the requested workflow end to end, including CLI/API/UI wiring when applicable.",
        "files": "Core Python package, FastAPI routes, React UI, tests, docs, and handoff files as needed.",
    },
    "fix-bundle-error": {
        "goal": "Diagnose and fix a Databricks Asset Bundle issue with local-first validation.",
        "task": "Inspect local bundle metadata and error output, identify the smallest safe fix, and validate against the dev target.",
        "files": "Bundle config, resource YAML, Python job/app files, tests, docs, and handoff files as needed.",
    },
    "add-databricks-app": {
        "goal": "Add or improve a Databricks App while keeping local development practical.",
        "task": "Implement the app structure, local entrypoints, deployment metadata, tests, and documentation needed for the requested app.",
        "files": "App entrypoint files, app.yaml, supporting Python or frontend files, tests, docs, and handoff files as needed.",
    },
    "write-tests": {
        "goal": "Add focused regression tests around the requested behavior.",
        "task": "Identify the behavior under test, add deterministic tests, and run the narrowest useful validation commands.",
        "files": "Test files and the minimum production code needed to make the tests pass.",
    },
}

DATABRICKS_EXTERNAL_DEPLOYER_CONSTRAINTS = (
    "This repo usually defines only dev target.",
    "stg/prd are handled by external deployer repo.",
    "Do not add stg/prd targets unless explicitly requested.",
    "Prefer local-first commands.",
    "Ask before execution.",
)

LOCAL_NOTE_CANDIDATES = (
    ".workbench/notes.md",
    "NOTES.md",
    "notes.md",
)

RECENT_OUTPUT_DIR = ".workbench/command_outputs"
MAX_NOTE_CHARS = 2000
MAX_OUTPUT_CHARS = 2000


def generate_prompt(
    *,
    task_type: PromptTaskType = "add-workflow",
    task_description: str = "",
    root: Path | None = None,
    recent_command_outputs: list[str] | None = None,
) -> GeneratedPromptResult:
    base = (root or Path.cwd()).resolve()
    detection = detect_project(base)
    defaults = TASK_DEFAULTS[task_type]
    project_summary = _project_summary(detection)
    command_outputs = _selected_command_outputs(base, recent_command_outputs or [])
    local_notes = _local_notes(base)
    validation_commands = _validation_commands(base, detection)

    description = task_description.strip() or defaults["task"]
    expected_files = defaults["files"]
    prompt = _render_sections(
        {
            "Goal": f"{defaults['goal']}\n\nSpecific request: {description}",
            "Current repo context": "\n".join(
                _compact_lines(
                    [
                        project_summary,
                        local_notes,
                        command_outputs,
                    ]
                )
            ),
            "Constraints": "\n".join(
                [
                    "- Keep changes scoped to the requested behavior.",
                    "- Do not read large source files unless they are selected or directly needed.",
                    "- Preserve unrelated user changes in the working tree.",
                    "- Prefer existing repository patterns over new abstractions.",
                ]
            ),
            "Company/security assumptions": "\n".join(
                [
                    "- Treat workspace files, Databricks configuration, and command output as sensitive.",
                    "- Do not include secrets, tokens, private hostnames, or customer data in prompts, docs, logs, or handoff files.",
                    "- Ask before running commands that deploy, mutate cloud state, or need network credentials.",
                ]
            ),
            "Databricks deployment strategy": "\n".join(
                f"- {line}" for line in DATABRICKS_EXTERNAL_DEPLOYER_CONSTRAINTS
            ),
            "Task": description,
            "Expected files to change": expected_files,
            "Validation commands": validation_commands,
            "Definition of done": "\n".join(
                [
                    "- Implementation matches the task and existing architecture.",
                    "- Tests cover the behavior at an appropriate level.",
                    "- Validation commands have been run or a clear blocker is documented.",
                    "- Documentation and handoff files are updated when behavior changes.",
                ]
            ),
            "Handoff update requirement": (
                "Before finishing, update `handoff/current.md` with current state, files changed, "
                "commands run, test results, open issues, constraints, do-not-change notes, and the next recommended Codex prompt."
            ),
        }
    )
    return GeneratedPromptResult(task_type=task_type, prompt=prompt, project_summary=project_summary)


def save_prompt(
    *,
    task_type: PromptTaskType = "add-workflow",
    task_description: str = "",
    root: Path | None = None,
    file_name: str | None = None,
    recent_command_outputs: list[str] | None = None,
) -> tuple[Path, str]:
    base = (root or Path.cwd()).resolve()
    result = generate_prompt(
        task_type=task_type,
        task_description=task_description,
        root=base,
        recent_command_outputs=recent_command_outputs,
    )
    prompts_dir = base / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    output_path = prompts_dir / _safe_prompt_file_name(file_name, task_type)
    output_path.write_text(result.prompt, encoding="utf-8")
    return output_path, result.prompt


def create_handoff(
    *,
    task_type: PromptTaskType = "add-workflow",
    task_description: str = "",
    root: Path | None = None,
    path: Path | None = None,
    recent_command_outputs: list[str] | None = None,
) -> tuple[Path, str]:
    base = (root or Path.cwd()).resolve()
    output_path = path or base / "handoff" / "current.md"
    detection = detect_project(base)
    prompt_result = generate_prompt(
        task_type=task_type,
        task_description=task_description,
        root=base,
        recent_command_outputs=recent_command_outputs,
    )
    content = _render_sections(
        {
            "Goal": task_description.strip() or TASK_DEFAULTS[task_type]["goal"],
            "Current State": _project_summary(detection),
            "Architecture Decisions": "\n".join(
                [
                    "- Keep command and prompt generation local-first.",
                    "- Generate Codex prompts from project detection, selected command output, and local notes instead of broad source scans.",
                    "- Keep Databricks stg/prd deployment outside this repo unless explicitly requested.",
                ]
            ),
            "Files Changed": "- Update this section during the active implementation session.",
            "Commands Run": _selected_command_outputs(base, recent_command_outputs or [])
            or "- No command output selected yet.",
            "Test Results": "- Not run yet.",
            "Open Issues": "- None recorded.",
            "Next Recommended Codex Prompt": prompt_result.prompt,
            "Constraints": "\n".join(f"- {line}" for line in DATABRICKS_EXTERNAL_DEPLOYER_CONSTRAINTS),
            "Do Not Change": "\n".join(
                [
                    "- Do not add stg/prd Databricks bundle targets unless explicitly requested.",
                    "- Do not include secrets or private source snippets in handoff files.",
                    "- Do not execute deploy or cloud-mutating commands without approval.",
                ]
            ),
        },
        title="# Current Handoff",
        section_order=HANDOFF_SECTIONS,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return output_path, content


def show_handoff(*, root: Path | None = None, path: Path | None = None) -> tuple[Path, str]:
    base = (root or Path.cwd()).resolve()
    handoff_path = path or base / "handoff" / "current.md"
    return handoff_path, handoff_path.read_text(encoding="utf-8")


def _render_sections(
    values: dict[str, str],
    *,
    title: str | None = None,
    section_order: tuple[str, ...] = PROMPT_SECTIONS,
) -> str:
    lines: list[str] = []
    if title:
        lines.extend([title, ""])
    for index, section in enumerate(section_order):
        if index:
            lines.append("")
        lines.append(f"## {section}")
        lines.append("")
        lines.append(values[section].strip() or "- None.")
    return "\n".join(lines).rstrip() + "\n"


def _project_summary(detection: DetectionResult) -> str:
    lines = [
        "Project detection summary:",
        f"- Type: {detection.project.project_type}",
        f"- Root: {detection.project.root_path}",
        f"- Detected files: {', '.join(detection.project.detected_files) if detection.project.detected_files else 'none'}",
    ]
    if detection.databricks_bundle:
        lines.extend(
            [
                f"- Bundle file: {detection.databricks_bundle.bundle_file}",
                f"- Databricks targets: {', '.join(detection.databricks_bundle.targets) if detection.databricks_bundle.targets else 'none'}",
                f"- Only dev target: {detection.databricks_bundle.only_dev_target}",
                f"- Deployment strategy: {detection.databricks_bundle.deployment_strategy}",
            ]
        )
    lines.append(f"- Message: {detection.message}")
    return "\n".join(lines)


def _validation_commands(base: Path, detection: DetectionResult) -> str:
    commands = suggest_commands(base)
    if commands:
        return "\n".join(f"- `{command.command} {' '.join(command.args)}`" for command in commands)

    if detection.project.project_type == "node_project":
        return "- `npm test`\n- `npm run build`"

    if detection.project.project_type in {"python_project", "databricks_app"}:
        return "- `pytest`"

    return "- Run the narrowest relevant local test or build command for the changed files."


def _local_notes(base: Path) -> str:
    for relative_path in LOCAL_NOTE_CANDIDATES:
        path = base / relative_path
        if path.exists() and path.is_file():
            text = path.read_text(encoding="utf-8")[:MAX_NOTE_CHARS].strip()
            if text:
                return f"Local notes from `{relative_path}`:\n{text}"
    return "Local notes: none found."


def _selected_command_outputs(base: Path, selected_outputs: list[str]) -> str:
    snippets = [output.strip()[:MAX_OUTPUT_CHARS] for output in selected_outputs if output.strip()]
    if not snippets:
        snippets = _recent_output_files(base)

    if not snippets:
        return "Selected recent command output: none available."

    return "\n\n".join(
        f"Selected recent command output {index + 1}:\n```text\n{snippet}\n```"
        for index, snippet in enumerate(snippets[:3])
    )


def _recent_output_files(base: Path) -> list[str]:
    output_dir = base / RECENT_OUTPUT_DIR
    if not output_dir.exists():
        return []
    paths = sorted(
        [path for path in output_dir.iterdir() if path.is_file()],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return [path.read_text(encoding="utf-8")[:MAX_OUTPUT_CHARS].strip() for path in paths[:3]]


def _safe_prompt_file_name(file_name: str | None, task_type: PromptTaskType) -> str:
    if file_name:
        safe_name = Path(file_name).name
        return safe_name if safe_name.endswith(".md") else f"{safe_name}.md"
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{task_type}.md"


def _compact_lines(lines: list[str]) -> list[str]:
    return [line for line in lines if line.strip()]
