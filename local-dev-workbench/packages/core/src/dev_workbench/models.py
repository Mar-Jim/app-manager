from typing import Literal

from pydantic import BaseModel

RiskLevel = Literal["low", "medium", "high", "destructive"]


class HealthStatus(BaseModel):
    status: str
    app: str
    version: str


class ProjectInfo(BaseModel):
    root_path: str
    project_type: str
    detected_files: list[str]


class DatabricksBundleInfo(BaseModel):
    bundle_file: str
    targets: list[str]
    only_dev_target: bool
    deployment_strategy: str


class DetectionResult(BaseModel):
    project: ProjectInfo
    databricks_bundle: DatabricksBundleInfo | None = None
    message: str


class GeneratedCommand(BaseModel):
    id: str
    label: str
    command: str
    args: list[str]
    working_dir: str
    risk_level: RiskLevel
    reason: str
    requires_confirmation: bool


class CommandRunRequest(BaseModel):
    command_id: str
    yes: bool = False


class CommandRunResult(BaseModel):
    command_id: str
    status: str
    stdout: str
    stderr: str
    exit_code: int | None
    started_at: str
    ended_at: str
