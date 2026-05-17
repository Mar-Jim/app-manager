from typing import Literal

from pydantic import BaseModel

RiskLevel = Literal["low", "medium", "high", "destructive"]
ProjectCreateKind = Literal["bundle-job", "bundle-pipeline", "bundle-sql", "bundle-dashboard"]
PromptTaskType = Literal["add-workflow", "fix-bundle-error", "add-databricks-app", "write-tests"]


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


class ProjectCreateRequest(BaseModel):
    kind: ProjectCreateKind
    name: str
    output_dir: str | None = None
    force: bool = False
    include_github_action: bool = False
    deployment_strategy: str = "external-deployer"
    target: str = "dev"
    dry_run: bool = True


class ProjectCreateResult(BaseModel):
    kind: ProjectCreateKind
    name: str
    root_path: str
    dry_run: bool
    created: bool
    files: list[str]
    conflicts: list[str]


class PromptGenerateRequest(BaseModel):
    task_type: PromptTaskType = "add-workflow"
    task_description: str = ""
    recent_command_outputs: list[str] = []


class GeneratedPromptResult(BaseModel):
    task_type: PromptTaskType
    prompt: str
    project_summary: str


class PromptSaveRequest(PromptGenerateRequest):
    file_name: str | None = None


class PromptSaveResult(BaseModel):
    path: str
    prompt: str


class HandoffCreateRequest(BaseModel):
    task_type: PromptTaskType = "add-workflow"
    task_description: str = ""
    recent_command_outputs: list[str] = []


class HandoffResult(BaseModel):
    path: str
    content: str
