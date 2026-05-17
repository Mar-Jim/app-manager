from pathlib import Path

from dev_workbench.models import ProjectDetection


MARKERS: dict[str, str] = {
    "databricks.yml": "databricks_asset_bundle",
    "app.yaml": "databricks_app",
    "pyproject.toml": "python_project",
    "package.json": "node_project",
    "handoff/current.md": "codex_handoff",
}


def detect_project(root: Path | None = None) -> ProjectDetection:
    base = (root or Path.cwd()).resolve()
    found = [marker for marker in MARKERS if (base / marker).exists()]
    project_type = MARKERS[found[0]] if found else "unknown"
    message = "Detected local project markers." if found else "No known project markers detected."
    return ProjectDetection(root=str(base), project_type=project_type, markers=found, message=message)
