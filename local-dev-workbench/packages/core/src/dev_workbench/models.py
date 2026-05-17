from pydantic import BaseModel


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
    command: list[str]
    risk: str
    requires_approval: bool = True
