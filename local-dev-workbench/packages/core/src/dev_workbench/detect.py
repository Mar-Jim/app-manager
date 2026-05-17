from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dev_workbench.models import DatabricksBundleInfo, DetectionResult, ProjectInfo


BUNDLE_FILES = ("databricks.yml", "databricks.yaml")
DATABRICKS_APP_ENTRYPOINTS = ("app.py", "main.py")
PACKAGE_FILES = ("pyproject.toml", "package.json", "setup.py", "setup.cfg")
VSCODE_EXTENSION_FIELDS = ("activationEvents", "contributes", "engines")


def detect_project(root: Path | None = None) -> DetectionResult:
    base = (root or Path.cwd()).resolve()
    detected_files = _detect_files(base)
    bundle_file = _first_existing(base, BUNDLE_FILES)

    databricks_bundle = _detect_databricks_bundle(base, bundle_file) if bundle_file else None
    project_type = _detect_project_type(base, bundle_file)
    message = "Detected local project type." if project_type != "unknown" else "No known project markers detected."

    return DetectionResult(
        project=ProjectInfo(
            root_path=str(base),
            project_type=project_type,
            detected_files=detected_files,
        ),
        databricks_bundle=databricks_bundle,
        message=message,
    )


def _detect_files(base: Path) -> list[str]:
    candidates = (*BUNDLE_FILES, "app.yaml", *DATABRICKS_APP_ENTRYPOINTS, *PACKAGE_FILES)
    return [candidate for candidate in dict.fromkeys(candidates) if (base / candidate).exists()]


def _detect_project_type(base: Path, bundle_file: Path | None) -> str:
    if bundle_file:
        return "databricks_asset_bundle"

    if (base / "app.yaml").exists() and (
        any((base / entrypoint).exists() for entrypoint in DATABRICKS_APP_ENTRYPOINTS)
        or any((base / package_file).exists() for package_file in PACKAGE_FILES)
    ):
        return "databricks_app"

    package_json = base / "package.json"
    if package_json.exists() and _is_vscode_extension(package_json):
        return "vscode_extension"

    if (base / "pyproject.toml").exists():
        return "python_project"

    if package_json.exists():
        return "node_project"

    return "unknown"


def _detect_databricks_bundle(base: Path, bundle_file: Path) -> DatabricksBundleInfo:
    bundle_data = _load_yaml_mapping(bundle_file)
    targets_data = bundle_data.get("targets", {})
    targets = _order_targets(list(targets_data)) if isinstance(targets_data, dict) else []
    only_dev_target = targets == ["dev"]

    if only_dev_target:
        deployment_strategy = "local_dev_external_deployer_candidate"
    elif {"dev", "stg", "prd"}.issubset(targets):
        deployment_strategy = "local_multi_target"
    else:
        deployment_strategy = "custom_targets"

    return DatabricksBundleInfo(
        bundle_file=str(bundle_file.relative_to(base)),
        targets=targets,
        only_dev_target=only_dev_target,
        deployment_strategy=deployment_strategy,
    )


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError:
        return _fallback_parse_bundle_targets(path)

    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def _fallback_parse_bundle_targets(path: Path) -> dict[str, Any]:
    targets: dict[str, dict[str, Any]] = {}
    in_targets = False
    target_indent: int | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue

        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if stripped == "targets:":
            in_targets = True
            target_indent = None
            continue

        if not in_targets:
            continue

        if target_indent is not None and indent < target_indent:
            break

        if stripped.endswith(":") and not stripped.startswith("-"):
            if target_indent is None:
                target_indent = indent
            if indent == target_indent:
                targets[stripped[:-1].strip("'\"")] = {}

    return {"targets": targets}


def _is_vscode_extension(package_json: Path) -> bool:
    try:
        data = json.loads(package_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False

    if not isinstance(data, dict):
        return False

    engines = data.get("engines")
    has_vscode_engine = isinstance(engines, dict) and "vscode" in engines
    has_extension_field = any(field in data for field in VSCODE_EXTENSION_FIELDS if field != "engines")
    return has_vscode_engine or has_extension_field


def _first_existing(base: Path, names: tuple[str, ...]) -> Path | None:
    for name in names:
        path = base / name
        if path.exists():
            return path
    return None


def _order_targets(targets: list[str]) -> list[str]:
    preferred = {"dev": 0, "stg": 1, "prd": 2}
    return sorted(targets, key=lambda target: (preferred.get(target, 100), target))
