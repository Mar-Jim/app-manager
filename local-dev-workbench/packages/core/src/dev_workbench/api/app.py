from pathlib import Path

from fastapi import FastAPI, HTTPException

from dev_workbench import __version__
from dev_workbench.commands import CommandExecutionError, run_command, suggest_commands
from dev_workbench.detect import detect_project
from dev_workbench.models import (
    CommandRunRequest,
    CommandRunResult,
    DetectionResult,
    GeneratedCommand,
    GeneratedPromptResult,
    HandoffCreateRequest,
    HandoffResult,
    HealthStatus,
    PromptGenerateRequest,
    PromptSaveRequest,
    PromptSaveResult,
    ProjectCreateRequest,
    ProjectCreateResult,
)
from dev_workbench.prompts import create_handoff, generate_prompt, save_prompt, show_handoff
from dev_workbench.projects import ProjectCreateError, create_project


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
        return suggest_commands()

    @api.get("/api/commands/suggest", response_model=list[GeneratedCommand])
    def commands_suggest() -> list[GeneratedCommand]:
        return suggest_commands()

    @api.post("/api/commands/run", response_model=CommandRunResult)
    def commands_run(request: CommandRunRequest) -> CommandRunResult:
        try:
            return run_command(request.command_id, yes=request.yes)
        except CommandExecutionError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @api.post("/api/projects/create", response_model=ProjectCreateResult)
    def projects_create(request: ProjectCreateRequest) -> ProjectCreateResult:
        try:
            result = create_project(
                kind=request.kind,
                name=request.name,
                output_dir=Path(request.output_dir) if request.output_dir else None,
                force=request.force,
                include_github_action=request.include_github_action,
                deployment_strategy=request.deployment_strategy,
                target=request.target,
                dry_run=request.dry_run,
            )
            return ProjectCreateResult(**result)
        except ProjectCreateError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @api.post("/api/prompts/create", response_model=GeneratedPromptResult)
    def prompts_create(request: PromptGenerateRequest) -> GeneratedPromptResult:
        return generate_prompt(
            task_type=request.task_type,
            task_description=request.task_description,
            recent_command_outputs=request.recent_command_outputs,
        )

    @api.post("/api/prompts/save", response_model=PromptSaveResult)
    def prompts_save(request: PromptSaveRequest) -> PromptSaveResult:
        path, prompt = save_prompt(
            task_type=request.task_type,
            task_description=request.task_description,
            file_name=request.file_name,
            recent_command_outputs=request.recent_command_outputs,
        )
        return PromptSaveResult(path=str(path), prompt=prompt)

    @api.post("/api/handoff/create", response_model=HandoffResult)
    def handoff_create(request: HandoffCreateRequest) -> HandoffResult:
        path, content = create_handoff(
            task_type=request.task_type,
            task_description=request.task_description,
            recent_command_outputs=request.recent_command_outputs,
        )
        return HandoffResult(path=str(path), content=content)

    @api.get("/api/handoff/current", response_model=HandoffResult)
    def handoff_current() -> HandoffResult:
        try:
            path, content = show_handoff()
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="handoff file not found") from exc
        return HandoffResult(path=str(path), content=content)

    return api


app = create_app()
