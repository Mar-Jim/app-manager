from fastapi import FastAPI

from dev_workbench import __version__
from dev_workbench.commands import list_generated_commands
from dev_workbench.detect import detect_project
from dev_workbench.models import DetectionResult, GeneratedCommand, HealthStatus


def create_app() -> FastAPI:
    api = FastAPI(title="Local Dev Workbench", version=__version__)

    @api.get("/health", response_model=HealthStatus)
    def health() -> HealthStatus:
        return HealthStatus(status="ok", app="local-dev-workbench", version=__version__)

    @api.get("/api/project/detect", response_model=DetectionResult)
    def project_detect() -> DetectionResult:
        return detect_project()

    @api.get("/api/commands", response_model=list[GeneratedCommand])
    def commands() -> list[GeneratedCommand]:
        return list_generated_commands()

    return api


app = create_app()
