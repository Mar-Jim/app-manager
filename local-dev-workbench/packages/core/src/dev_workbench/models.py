from pydantic import BaseModel


class HealthStatus(BaseModel):
    status: str
    app: str
    version: str


class ProjectDetection(BaseModel):
    root: str
    project_type: str
    markers: list[str]
    message: str


class GeneratedCommand(BaseModel):
    id: str
    label: str
    command: list[str]
    risk: str
    requires_approval: bool = True
